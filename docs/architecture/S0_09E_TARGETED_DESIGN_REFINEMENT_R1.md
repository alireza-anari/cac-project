# CAC — S0-09E Targeted Design Refinement R1

**Date:** 2026-11-06  
**Role:** Astra Management / Architecture & Security  
**Tracking:** [Issue #23](https://github.com/alireza-anari/cac-project/issues/23)  
**Parent proposal:** [S0-09E anti-rollback design](S0_09E_ANTI_ROLLBACK_DESIGN_PROPOSAL.md), blob `5c24e2034f539d3a6f6c59903c78ae17abcb01bd`  
**Review input:** [S0-09E independent review at Draft PR #24](https://github.com/alireza-anari/cac-project/blob/dda6fea3347e582dfdcfc27299fbc8336b7233a0/docs/security/S0_09E_DESIGN_READ_ONLY_REVIEW.md), findings E-P0-01..04 / E-P1-01..03 / E-P2-01  
**Observed predecessor:** [S0-09D ruling](S0_09D_ARCHITECTURE_RULING.md): real C anchor rollback revives old owner (FAIL_SECURITY)  
**Disposition:** `DESIGN_REFINEMENT_R1_PROPOSED / NOT_AUTHORIZED_FOR_POC / P0_SECURITY_BLOCKED`

This document supplements the **existing** S0-09E proposal rather than replacing its provenance or rewriting completed C/D experiments. It tightens the *required contract and experimental boundaries*, but does **not** prove that a suitable external root, verifier, actor admission or safe reconciliation implementation exists. No W test has been run.

## Decision: retain W candidate, narrow claims

Continue to evaluate an independent monotonic W authority with online authorization, not another restorable C. Evaluate key/identity rotation and complete fail-closed pause as alternatives. **No vendor, KMS, consensus implementation, cryptographic wire format, TTL, Production topology or integration task is approved.**

The present proposal's universal claim (“no rollback/clone may ever revive authority”) is **NOT ESTABLISHED**. Separate three classes:

- **Supported future restore boundary (to be proven):** A/B/C logical restoration against an *unchanged, independently trusted current W root and enforced current verifier policy*. Require denial of A's fresh issuance/RLS after B takes over.
- **W-root disaster recovery / simultaneous restore of all trusted material:** **UNSUPPORTED / BLOCKED** until an independently governed nonrollback continuity mechanism is specified and audited. An old W signer with restored old epoch and restored trust policy can produce a *freshly signed wrong answer*. Linearizability, a TLS key, a database system identifier or a second ordinary restorable database does not solve this.
- **Physical clone, privileged administrator, loss of root custody:** distinct scoped threats. No promises against excluded control of verifier, SQL/RLS superuser, or every W custodian. An actor able to rewrite both authority root and trusted verifier policy is initially out of scope; the production threat boundary and operator separations still require later ratification.

### E-P0-01 — W continuity and irreversibility contract

A credible W proposal **MUST** identify an external, durable **continuity fact** `root_id, namespace_id, incarnation, committed_high_watermark, root_policy_version` or an equivalent verifiable commitment that:
1. Is read/checked through a trusted path independently of any restorable C/A/B state, and is not regenerated merely by restoring the W data snapshot.
2. Moves monotonically at a specified durable linearization point **before an activation/revocation becomes usable**. An authority must not sign or attest an epoch inconsistent with this fact.
3. Separately protects the current signing/verification policy. Retired signer roots cannot be revived by restoring an older root-policy cache; an independent verifier must reject W signer/namespace discontinuity and old key policy.
4. Specifies exactly which W member data, backups, keys and namespace bootstrap actions may be restored while the continuity fact remains intact. An all-members snapshot restore, W namespace recreation or rollback of both commitment and trust material must cause **NOT_READY / DENY** unless its safety is *independently* demonstrated.
5. Defines the trusted institution/device/quorum/root which can change this fact and the failure domain/privileged operator who cannot. **If no such independent root is available, do not claim rollback-safe recovery; use explicit indefinite pause.**

This specifies *what to prove*, not a hidden assumption that a generic quorum or extra PostgreSQL database satisfies it. No W-root capability is marked PASS.

### E-P0-02 — Verifier, actor and supported restore admission

Define a **supported installation manifest** (source/build ID, database migration fingerprint, exact guard entrypoints, enabled RLS/ownership/grants, minimum accepted verifier policy/key epoch, trusted W root identity, signed administrative approval) protected by a control path **not restored with A/B/C**. Before any restored app/guard/issuer can become READY, compare its measured/attested runtime to that manifest and independently confirm W admission. A former C-only or pre-W guard version is **QUARANTINED / DENY**, not migrated automatically into trust. Do not claim that an administrator with unrestricted DB superuser ability is constrained by PostgreSQL RLS.

Every supported SQL/function, direct issuer, PgBouncer backend and read/write path must be covered; no recovery switch, public bypass grant, offline permit, alternate prior verifier or stale signing key fallback. A copied verifier **public** key cannot confer signing authority. Trust-policy and root-key retirement must survive the same restore scope the verifier is asked to validate.

Separate **logical owner** from **physical actor incarnation**. A PostgreSQL SID, DNS name, restored machine ID or copied software credential does not uniquely identify a physical clone. Candidate actor enrollment must use an independent W-issued single-active admission credential/proof bound to a specific incarnation, with a documented revocation/hard-fence path and separate root custody. **Without nonclonability or independent exclusion of copied actors, same-identity physical clones remain BLOCKED.** The design may instead explicitly exclude physical clones from the first narrowly supported restore mode; no broader clone-safety claim then follows.

### E-P0-03 — Operation lifecycle and local COMMIT ordering

The proposed W must serialize on one namespace:
- **ADMIT/OPEN:** atomically verify `ACTIVE(owner,e)`, no `REVOKING` barrier, and required actor/operation identity; *durably commit* an intent `op_id, digest, epoch, actor_incarnation, local_tx_binding, state=OPEN` **before** returning the initial authorization permit. Unacknowledged admission means the caller must query W using the *same* operation/digest and deny until resolved.
- **USE:** the guard must verify the admitted operation is current and bound to the exact authorized local transaction, operation intent and verified actor. Permits delayed from before `REVOKING` cannot begin a new local transaction after revocation; first use needs a fresh W check under the same durable hold. No backend PID/xid alone counts as physical actor identity.
- **REVOKE_INTENT:** a serialized W transition immediately prevents **new** old-owner admissions. It does not discard, time out or silently close existing holds. The old owner can be prohibited from starting further work while its already-admitted local transactions remain unresolved.
- **CLOSE:** an operation may transition to `CLOSED_COMMIT` / `CLOSED_ABORT` only after **trustworthy, durable, transaction-specific** local outcome/effects evidence, linked to its operation/DB incarnation and actual committed transaction. A broker's lost connection, a client timeout, an old local snapshot, a missing session or W leader restart is **not** such evidence. If the commit ACK is lost and outcome cannot be established, preserve `OPEN_UNKNOWN`.
- **PROMOTE:** W may reserve a next epoch during a revoke-intent but may **not mark its successor READY or issue a live successor permit** while any old `OPEN/OPEN_UNKNOWN` could still commit, unless separately approved hard-fencing plus a provably safe outcome/effect resolution has been completed and durably recorded at W.

**Safety-ordering assertion:** `successor READY` must never coexist with an older authorized local transaction that could still durably COMMIT. Admission and revoke-intent are one serializable/CAS order; closing a hold is a separate, positively proven durable event. A final guard check *before* local COMMIT is insufficient without a hold that survives until outcome. PostgreSQL prepared transactions (if ever supported) must be explicitly accounted for or prohibited and tested.

**Crash cuts for future proof:** before/after OPEN commit and ACK, permit delivery, first use, local commit/abort, lost outcome ACK, W close and successor READY; including same PID reused by PgBouncer and W leader/transport failure. W outage or unverifiable root state denies **new** permits; unresolved operations block new owner regardless of availability.

### E-P0-04 — Revocation versus orphan reconciliation

Use separate W meanings:
- `REVOKING(e)`: no *new* authorization from old actor, but in-flight outcomes may still exist.
- `FENCED_UNRESOLVED(e, op)`: independent old-actor fencing evidence is registered, but local outcome or side effects remain ambiguous; **not READY** for successor where ambiguity could affect authorization/effects.
- `SUCCESSOR_READY(e+1)`: permitted only after all prior operations have trustworthy completed/aborted effects or a separately reviewed proof establishes no old operation can act/commit and reconciliation preserves invariants.

An operator signature confirms who approved a case, **not** whether a local COMMIT happened. A restored application/issuer ledger alone is not a sufficient outcome witness. To clear an orphan, the eventual standalone ADR must specify positive local transaction/effect evidence bound to operation, database/timeline/incarnation and external side effects; independently verified hard fencing; single-use idempotent W CAS resolution; conflict/replay denial; receipt/tombstone nonrollback retention; and high-risk operator separation of duties. Unresolvable histories **remain blocked indefinitely**. Never interpret session disappearance, TTL, elapsed wall clock, a guessed outcome or fixture reset as permission to clear OPEN.

**Decision for first candidate experiment: EXCLUDE orphan clearing.** Only `OPEN_UNKNOWN -> DENY/BLOCKED` may be tested, not marked “recovered”. Proving safe resolution/availability is a separate later architecture gate. A manually initiated release without trustworthy outcome evidence is also prohibited.

## P1/P2 refinements incorporated as future requirements

- **E-P1-01:** authentication transcript must include domain/protocol version, W root+policy epoch, namespace, logical owner, actor incarnation, action/intent digest, local cluster+boot+transaction identity, unique operation ID and nonce-use state. A signature is provenance, not proof of current authority. Strict verifier policy, root retirement and replay rules required; no crypto algorithm, serialization or TTL ratified.
- **E-P1-02:** durable idempotency-key + request-digest binding; same key/different intent **REJECT**; ambiguous write response leads to linearizable status lookup with same key, not guessed success or second epoch. Retain tombstones/resolution receipts across any *supported* W recovery.
- **E-P1-03:** distinguish **GREEN negative denial under an actual outage** from **RED assertion when enforcement is deliberately disabled**. Specify current/noncurrent W signer, stale valid-signed response, late delivery, one-way loss, W unavailability before local COMMIT, old/clone actor, and guard downgrade schedules. Restoration-only GREEN is not proof the control is sensitive.
- **E-P2-01:** claim ledger must version parent C/D evidence `129 distinct GREEN`, inherited original C-root rollback safety **FAIL_SECURITY**, new candidate W-path invariant **NOT_RUN**, supported versus excluded restore modes, and explicit expected RED/GREEN controls. Do not make legacy tests pass by C-only fallback.

## Narrow potential future PoC, NOT YET AUTHORIZED

**Lane 1 — W integration/deny-only model (if approved later):** a clearly labeled *assumed-consistent W oracle* (not root implementation) to test end-to-end guarded admission, restored C rejection, CAS, operation hold through local durable COMMIT, delay/lost ACK, stale actor and PgBouncer reuse. Any observed GREEN says only that the integration works **under the W oracle assumption**. It **does not** establish W anti-rollback, disaster recovery or orphan release.

**Lane 2 — independent root-of-trust recovery proof:** a separately reviewed real W continuity/custody design and restore/rebootstrap experiments, including W snapshot rollback with old signer credentials and restored verifier, physical clone and partitions. Unless actual support exists, mark `NOT_RUN/BLOCKED` rather than inferring success from Lane 1. Do not synthesize an unproven “hardware root” in CI and call it real.

**Lane 3 — orphan reconciliation:** deferred, no proposed code or destructive clearing until positive outcome/effect and old-actor hard-fencing proof is independently accepted. Status `BLOCKED`.

No lane is authorized to execute by this document. Before considering Lane 1, require an independent review of this refinement and an explicit scoped Management vote identifying assumed versus proven properties, test RED controls and which 129 previous regressions are retained. Any original `test_anchor_rollback_must_not_revive_previous_owner` must remain present and its **legacy path remains FAIL_SECURITY**; prove a separate W-enforced path without tampering with that assertion or changing its meaning.

## Current governance

`E-P0-01/02/03/04: DESIGN CONTRACT PROPOSED; SECURITY PROOF BLOCKED`. All W experimental evidence `NOT_RUN`; S0-09D C rollback `FAIL_SECURITY`. Preserve `NEW_IMPLEMENTATION_EXPERIMENTAL / PROTOCOL_PROPOSED`. [Issue #23](https://github.com/alireza-anari/cac-project/issues/23) OPEN, baseline [#9](https://github.com/alireza-anari/cac-project/issues/9) OPEN, [SOURCE-001 #1](https://github.com/alireza-anari/cac-project/issues/1) and `GATE-SOURCE` BLOCKED. Draft PRs #11/#16/#18/#20/#22/#24 unmerged; no change to APR-033/034/035/036, no Production, real identity/onboarding, KMS choice, key contract, Sprint 0 completion or source-baseline promotion.

**Management request:** targeted second **read-only** review of this addendum. It may confirm that the *boundaries and failure handling* are now adequately explicit to ask for a later, assumption-labeled Lane 1 PoC; it cannot certify the W root or mark the P0 security result resolved.
