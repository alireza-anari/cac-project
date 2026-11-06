# CAC — S0-09E: Non-Rollback Authority & Orphan Recovery — Architecture Proposal

**Date:** 2026-11-06  
**Owner:** Astra Management / Architecture & Security  
**Tracking:** [Architecture Issue #23](https://github.com/alireza-anari/cac-project/issues/23)  
**Evidence:** [S0-09D ruling](S0_09D_ARCHITECTURE_RULING.md), [S0-09D handoff](https://github.com/alireza-anari/cac-project/blob/ca043e2751ea1dbcb7aed3c1ed3d171a9bb1f0e2/docs/S0_09D_HANDOFF.md)  
**State:** `DESIGN_CANDIDATE_SELECTED_FOR_INDEPENDENT_REVIEW / PROTOCOL_PROPOSED / SECURITY_PROOF_NOT_ESTABLISHED`  
**Classification:** DOCUMENTATION ONLY; not implementation authorization, not a protocol ratification, and not approval of a KMS/vendor/production topology.

## 1. Why the current system cannot pass the gate

S0-09D executed an actual logical rollback of anchor C's schema from epoch 2 to epoch 1 **without changing C's PostgreSQL system identity**. Its old owner A regained readiness, issued a *new* context and accessed scoped data; current owner B became unready. The fail-closed safety assertion remained RED and this mode is `FAIL_SECURITY / BLOCKED`, even though workflows reported SUCCESS for correctly detecting that unsafe outcome.

The S0-09C/D independent C cluster, signed attestation, online SQL gate, nonce, CAS and OPEN ledger are **not** an independent anti-rollback root if the authoritative C epoch and signing material are themselves restored. A schema restore cannot be permitted to rewrite the highest committed authorization generation. Ordinary PostgreSQL WAL durability, one server identifier or copied HMAC credentials do not supply this guarantee.

## 2. Architecture decision candidates

| Candidate | Safety approach | Limitation / trust obligation | Disposition |
|---|---|---|---|
| **A. External monotonic authority witness W** | An independently governed, linearizable root records high-watermark epoch, owner, revocation and unresolved operations; each sensitive transaction must get fresh, authenticated W proof, checked by guard rather than trusting C alone | Requires non-rollback durable W state, root identity/key custody separate from C and application restores, a consistent quorum/failure domain and fencing of all old signers. W outage means DENY; W rollback itself needs a root-of-trust explanation | **Preferred isolated proof candidate**, not an accepted Production design |
| B. New authority identity/key epoch plus hard-fence | Rotate root/signing authority after restore; make every old key, endpoint and signer provably unable to authorize | Merely rotating a DB key is insufficient: old still-active actors/DB clones may use old material unless an independent non-rollback authority enforces key invalidation. Requires an external root equivalent to A, and physical fencing | Alternative to compare in ADR; not selected for direct implementation |
| C. Manual permanent recovery stop | Refuse all authority operation after C rollback/suspect restore until independent incident investigation and re-established root | Availability loss and manual coordination; safe only if all old endpoints/keys cannot authorize during the stop | **Fallback fail-closed operating mode**; never silently reactivate from a backup |

**Proposed choice for a narrow experiment:** A, with C retained as a disposable coordinator/cache of nonauthoritative local state. W—not PostgreSQL C—is the *sole* authority for the latest epoch and current owner. No specific W vendor, consensus library, KMS or external infrastructure is selected. W cannot share the rollback, administrator or backup control plane of C/A/B. A single extra PostgreSQL database on the same CI host does not meet that production trust boundary.

### W assumptions that cannot be hidden

1. W provides **linearizable** state transition and fresh-read semantics for a single authority namespace. The chosen root must prevent rollback/cloning of committed epoch state within the agreed threat model; otherwise it is **another version of C** and the design fails.
2. W endpoint and response identity are authenticated end-to-end; its signing/private credentials and trust-anchor rotation are not restored with application/C backups. Current SQL guard or an independently trusted verifier must validate the W response with a fresh nonce, epoch, owner, operation ID and local DB transaction binding.
3. Any W outage, stale read, unverifiable signature, ambiguous commit result, same-identity clone conflict or lack of monotonic-proof continuity results in **DENY and NOT_READY**. No offline cached W authorization, grace period, automatic fail-open or assumption that a valid C HMAC is enough.
4. A privileged actor able to rewrite W quorum/hardware root **and** its trusted credentials is outside the initial bounded proof; this residual trust must be explicit, operationally constrained and separately approved. A production choice must have a documented disaster-recovery and non-rollback story for W itself.

## 3. Normative candidate security invariants (unapproved contract)

- **INV-01 — Monotonicity:** for any committed authority activation `epoch=e`, no older epoch `e'<e` can ever authorize new issuance, verification, activation or data access, even if C/A/B, keys or local ledger are restored/cloned.
- **INV-02 — Fresh end-to-end authority:** every guarded issuance/read has an online W-authenticated operation permit, bound to namespace, exact current epoch, owner identity, C/application identity, nonce, backend PID/transaction identifier and operation ID. The local guard validates the trusted W permit independently of any C-only signature. No permit is reusable across transactions, owners or pooled backend reuse.
- **INV-03 — Unique takeover:** W serializes ownership changes using CAS; a new owner cannot enter READY until older authorized operations are proven complete or the old actor has been hard-fenced and its outcomes conservatively reconciled. A stale C copy cannot lower W's high-watermark.
- **INV-04 — Fail closed on uncertainty:** W unavailable/untrusted, conflicting witness identities, lost activation ACK or unresolved operation -> NOT_READY/deny. Neither elapsed time nor disappearing `pg_stat_activity` alone establishes safe recovery.
- **INV-05 — Effective hard fence:** once W revokes an old owner/epoch, the old issuer/guard/pooled connection cannot obtain a fresh W permit; where a local transaction could commit after a decision, takeover must remain blocked by W-tracked operation holds until completion or externally proven fencing. A returned read cannot be retroactively revoked.
- **INV-06 — Identity and keys:** generation epoch and root-key identity must be bound to the independent W namespace. Physical same-system-ID clones are distinct *actors* unless separately registered; a copied C signing key or matching PostgreSQL system ID confers no root authority.
- **INV-07 — Audit and recovery:** authorization transition, OPEN creation and resolution are durably ordered at W; reconciliation is idempotent with immutable, signed/auditable evidence, never from a restored C ledger alone.

These are **required claims to prove**, not statements that the current code already satisfies.

## 4. Candidate state transitions

`UNINITIALIZED -> RESERVED(e) -> LOCALLY_APPLIED(e) -> ACK_VERIFIED(e) -> ACTIVE(e) -> READY(e)`

Each phase requires W-backed identity and monotonic epoch checks. An activation response is not a permit by itself; a guard may authorize only after an independently verified `ACTIVE(e)` W response, a currently valid operation hold, and local SQL scope checks.

Takeover to `e+1`:
1. W atomically records intent to revoke old owner. A stale C cannot choose a lower epoch.
2. W blocks new old-epoch permits. If any old authorization holds or durable orphan OPEN intents remain, **do not grant new READY** absent externally established safe fencing and outcome resolution.
3. Once W has durable proof of quiescence/fencing, allocate/commit `e+1` and new owner/key binding. A and B cannot both obtain live permits.
4. New B applies the generation to its independent local DB and proves committed state through an authenticated ACK; W confirms current owner and B enters READY only after a fresh W check.
5. Old A, old C, copied W proof and reused PgBouncer backends MUST fail a fresh guarded request. Restoring C to old `e` cannot change W `e+1`.

**Lost activation ACK:** retry using the same idempotency key; re-read *linearizable W* state. Never create a second epoch to guess the outcome, nor assume success based on the restored C state.

**Anchor C rollback after B activation:** a restored C may claim `e`, but W still holds `e+1`. The SQL guard obtains W proof via a root-authenticated path and denies A; B may also temporarily become unready until C is repaired. This is an intentional availability trade-off. If W can also be rolled back, the candidate **fails the invariant**.

## 5. Orphan OPEN: conservative recovery proposal

State model: `OPEN -> RESOLVED_KNOWN_COMMIT | RESOLVED_KNOWN_ABORT | FENCED_UNRESOLVED`. `FENCED_UNRESOLVED` is **not automatically safe to clear** or authorize a successor. Keep a durable W record of every unresolved operation and the associated owner/epoch, local transaction, intended scope and unique operation ID.

**Prerequisites before granting any new owner:**
1. A separately trusted W authority commits a higher/revoked epoch and proves the old actor is unable to obtain a permit; where needed, operations/credentials/network paths are actually hard-fenced, not merely declared expired.
2. Collect credible local transaction outcome evidence (commit record/ledger, database recovery state, externally committed audit witness); consider backups, replica lag, still-running/blocked transactions and ambiguous DB COMMIT ACK. If the outcome remains unknowable, **do not infer abort from a missing session**.
3. An authorized operator/recovery coordinator submits an immutable case ID with signed evidence and scope, with separation-of-duty for high-risk manual reconciliation. W serializes competing reconciliation attempts.
4. W writes a single-use durable reconciliation receipt tied to the unrecoverable operation, prior epoch and resolution reason. A stale C or retry cannot erase/overwrite it. Confirm both that no old authorization can commit and that application effects are reconciled/idempotent before releasing successor readiness.
5. If any condition is absent or W/identity is compromised, leave both authority and OPEN **BLOCKED**. No timeout auto-clear, old-owner revival or fixture-reset-as-operational-repair.

This defines **review requirements**, not an implementable verified clearing algorithm. A safe reconciliation algorithm needs a separate security review and independent execution proof.

## 6. Threat/failure decision matrix for the next proof

| Fault or adversarial condition | Required candidate outcome | Existing S0-09D evidence |
|---|---|---|
| Restore C from epoch2 to epoch1 with unchanged C identity | Old A cannot become ready, issue or use RLS; original unchanged safety assertion must become GREEN | **FAIL_SECURITY** (old A revived) |
| Restore/clone application A or B, copy old keys/tickets | Fresh W check rejects stale generation and transaction | Partial logical restore/pool evidence only |
| Roll back W itself or clone W's root identity/state | Root-of-trust policy detects and denies; otherwise candidate rejected | **NOT_RUN / DESIGN BLOCKER** |
| W unavailable, partitioned or returns stale proof | Deny all new guarded use; explicit availability loss | Partial C-stop/channel-refusal only |
| Two activation attempts, stale old broker and revived C | Only one W-committed owner; no simultaneous live authorization | Two-thread C CAS tested, not W |
| Lost COMMIT/activation ACK and retries | W idempotent and exact single committed outcome; uncertainty DENY | Application receipt-drop only; network ACK NOT_RUN |
| Orphan OPEN during issuer crash/restart | No unauthorized new permit; safe reconciliation only with independent proof | Fail-closed denial PASS; safe clearing BLOCKED |
| Physical same-identity PGDATA clone / PITR / replica promotion | Root identity and W fence prevent prior authority revival | **NOT_RUN** |
| Reused PgBouncer backend with old session state | Fresh W-bound transaction permit and scope; stale context denied | C-fenced pooled runtime PASS without W |
| Privileged C admin/DB restore vs W credentials | No authority to rewrite W epoch/keys | **NOT_RUN** |

## 7. Minimal isolated experimental proof plan (subsequent mission, not authorized yet)

- Draft a deterministic W test fixture with a *distinct* rollback-control and credential boundary from A/B/C, showing its limitations; do not label a single-host extra database as Production anti-rollback.
- Preserve unchanged 129 distinct previously passing cases **and the failing anchor rollback assertion**; compare that exact failing safety assertion under the candidate with and without fresh W enforcement.
- Prove mandatory RED for disabled W/rollback protection, real C-rollback `epoch2→1`, W outage, stale attestation and double-owner activation; require observable final GREEN for all supported modes only after restoration. Keep unsupported physical/multihost modes explicitly NOT_RUN.
- Include real transaction-mode PgBouncer replay, old in-flight commit vs W takeover, lost ACK/retry, orphan OPEN, and strict rollback/reapply of fixture schemas and permissions.
- Obtain independent read-only architecture/security review **before any implementation task**; use real PostgreSQL CI with exact Push and PR merge-ref SHAs after code authorization.
- No Production keys, public API, real IdP/MFA, onboarding, customer data, auto merge, source-baseline promotion or product security/TTL ratification.

## 8. Decision gate and governance

**Architecture proposal:** Conditional preference for **A: online W-backed monotonic authority**, subject to independent security review of the root's non-rollback guarantees, DB guard enforcement, single-active-owner protocol and conservative orphan-handling procedure. This is **design selection for review only** and does not resolve the P0 safety failure.

**Mandatory independent review questions:**
- How does W prove it cannot itself be restored behind a committed epoch? Which separate trust root and failure domains enforce that claim?
- Does a restored C or pooled runtime have any path to authorize using C-only credentials, stale W signatures or cached/expired permits?
- Can W change owner while a local A transaction can still commit? What exact mechanism prevents this, including loss of a COMMIT ACK?
- What evidence can resolve orphan OPEN without inferring a rollback/abort from vanished process state?
- Does the proposed receipt survive backups, retries, clone identity and split-brain?

**Disposition until proof:** `P0_FAIL_SECURITY_REMAINS / RECOVERY_PROTOCOL_PROPOSED / GATE_9_OPEN / SOURCE_001_BLOCKED / NO_MERGE`. Parent PRs #11/#16/#18/#20/#22 remain Draft and unmerged; APR-033/034/035/036 unchanged. An approved design *proposal* must not be interpreted as an implementation, validated protocol or Production recovery readiness.
