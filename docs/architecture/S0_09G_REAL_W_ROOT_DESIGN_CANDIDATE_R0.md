# CAC — S0-09G Architecture Candidate R0
## Independent Anti-Rollback Root, Authorization Continuity, and W Recovery

**Decision date:** 2026-11-06  
**Owner:** Astra Management / Architecture & Security  
**Tracking:** [S0-09G Architecture Issue #28](https://github.com/alireza-anari/cac-project/issues/28), parent [#23](https://github.com/alireza-anari/cac-project/issues/23)  
**Disposition:** `DESIGN_CANDIDATE_R0_FOR_INDEPENDENT_REVIEW / LANE2_NOT_AUTHORIZED / P0_SECURITY_BLOCKED`  
**Origin:** `NEW_IMPLEMENTATION_EXPERIMENTAL / PROTOCOL_PROPOSED`  
**Boundary:** DOCUMENTATION ONLY. This ADR proposal does not amend APR-033/034/035/036, implement a trust root, approve vendors/keys, close security gates, or authorize Production.

### Evidence and prior decisions (do not restart)

- [S0-09D final ruling](S0_09D_ARCHITECTURE_RULING.md) documents **actual P0 FAIL_SECURITY**: rollback of the C anchor schema from epoch2 to epoch1 with unchanged C PostgreSQL identity revived old owner A, which obtained fresh issuance and scoped RLS. The original safety assertion is unchanged.
- [S0-09E design R1](S0_09E_TARGETED_DESIGN_REFINEMENT_R1.md), [Lane1-scoped authorization](S0_09E_LANE1_SCOPED_AUTHORIZATION.md) and [S0-09F final ruling](S0_09F_ARCHITECTURE_RULING.md) bound the assumptions. S0-09F [Draft PR #27](https://github.com/alireza-anari/cac-project/pull/27) at `2bebe0022956809b3842a015d215e6332c5a8b0f` provided 129 inherited plus 40 new distinct GREEN observations across separate suites, with three mutation RED/GREEN controls. **W_ORACLE_ASSUMED** remains a lab fixture on the same CI host.
- **All real W anti-rollback, W-root restore and physical clone claims remain NOT_RUN/BLOCKED.** Lane3 orphan OPEN *reconciliation* remains BLOCKED. The original rollback failure does not become GREEN because a separately labelled W-oracle case passes.
- Pre-ABORT and lost ABORT/CLOSE-ACK cuts remain separately NOT_RUN even within the bounded Lane1 lifecycle.

## 1. Impossibility boundary: a signature cannot certify freshness

Consider two histories indistinguishable to a restored W and a restored verifier:
- **History H1:** owner A at epoch1 remains authoritative.
- **History H2:** B was committed owner at epoch2; later the W database, its private signing key, its namespace metadata **and** the verifier trust policy were all rolled back to epoch1.

In both, the restored signer can produce a **freshly signed** answer asserting epoch1. A signature establishes origin under a key, not whether a newer epoch was previously committed. A consensus cluster that can be entirely restored from an old snapshot can replay an internally consistent but stale state. An append-only audit store alone can preserve older records yet not make the *highest known committed head* available as a trusted, linearizable authorization decision. If all last-head, trust-root and signer-revocation material can be rolled back together, **no verifier confined to that restored material can distinguish H1 from H2**.

**Design consequence:** A true rollback-safe authority requires an independent *continuity/freshness fact* and a trusted enforcement path that cannot be reverted in any supported restore scope. If this fact or its trust anchor is lost, the safe state is `ROOT_UNVERIFIED / NOT_READY / DENY`, potentially indefinitely. This is an explicit availability sacrifice, not a recovery mechanism.

This is a threat-model argument, not an implementation/formal verification result. The privileged actor that can simultaneously rewrite **all** independent continuity roots and mandatory verifiers is excluded from the initial candidate claim; privileged exclusions must be governed, visible and separately approved.

## 2. Proposed partition of authority: W is not its own root

**Selected candidate for independent design review (not implementation):** separate the logical W transaction/operation service from an independently governed **continuity root R**. R must enforce an irreversible, linearizable, independently authenticated *latest authorization head* (or an equivalent primitive), with a separate administrative, backup and recovery control boundary from W, A, B and C. W replicas can be replaced or restored as caches/participants; the old W backup must not be allowed to sign current authority from its own snapshot.

**Required R state**, or a stronger equivalently authenticated commitment:
`(root_id, namespace_id, root_incarnation, seq, committed_epoch, owner_id, owner_actor_incarnation, signer_policy_version, revoked_key_epochs, approved_guard_manifest_version, op_ledger_head, unresolved_open_set_commitment, previous_head_digest, state)`.

The commitment is *not sufficient by itself* if an application cannot obtain a **fresh authenticated highest committed head** and cannot prove that its W operation ledger matches that head. A restored W lacking an operation history must enter quarantine, not reconstruct an empty OPEN set and resume. The full pending-operation evidence or a verifiable complete replay chain must survive independently of W's mutable snapshot.

### Principal responsibilities

| Boundary | Candidate responsibility | Must not be trusted to do |
|---|---|---|
| **R** independently governed root | Serialize and durably commit identity/epoch/owner/revoke/OPEN/close head transitions, current signer-policy/manifest retirement, fresh status; retain nonrollback continuity and complete unresolved-work commitments | Infer COMMIT from lost connection or automatically reinvent old epoch after restoration |
| **W** state/coordination layer | Reconstruct and verify against R, serve only admitted current actor operations, maintain operation details, refuse if replay incomplete; no current authority without R | Act as ultimate freshness root, sign from restored old snapshot alone, erase unknown OPEN |
| **Trusted verifier/guard** | Perform fresh R-root-authenticated current-head/permit check on supported SQL/issuer/RLS entry points, current guard/actor manifest check, enforce nonowner ACL/RLS and transaction binding | Accept C-only/warm-cache permit, old policy signer, copied PG system ID as identity, or a private key from application backup |
| **Actor A/B** | Prove current physical/admitted incarnation and bind operation and local transaction; obey old-actor hard fencing and observed outcome obligations | Self-declare clone identity or resolve unknown effects using an old ledger |
| **Recovery operator** | Approve human quarantine/escalation under separated duties and preserve evidence | Override R high-watermark, clear unknown OPEN by timer or signature alone, grant successor while commit possible |

A “root” which is merely **another** snapshot-restorable PostgreSQL cluster, the same backup account, a W-only revocation table or a trusted signer key recovered with W does **not** satisfy the R contract.

### Authenticated R decision response (draft contract, no wire/crypto choice)

A current decision/permit must bind `protocol_domain, root_id, namespace, root_incarnation, seq, committed_epoch, owner_id, physical_actor_incarnation, approved_guard_manifest, signer_policy_version, operation_id, idempotency_key_digest, intent_digest, local_DB_incarnation, local_transaction_binding, challenge_nonce, decision_kind, R_head_digest`. Validation must reject unknown root/policy, old signer epoch, cross-operation replay, unadmitted actor, stale first use, forged responder, reused backend and a delayed response obtained before REVOKING.

**Security caveat:** “signed” is not equal to “current”: the trusted verifier must obtain freshness against R's independently protected head, not just signature-check a stale W reply. A copied verifier public key has no signing powers, but a restored verifier may *trust an obsolete key* unless boot/admission policy independent of that restore blocks it.

## 3. Candidate alternatives and decision tradeoffs

| Option | Safety claim it might support | What can still go wrong | Tradeoff / recommendation |
|---|---|---|---|
| **A — Independently governed linearizable R with nonrollback current-head primitive** | Serialized current epoch, signer-policy retirement and durable OPEN history enforced outside W snapshots. No old-W-only attestation. | A quorum/consensus database's **own** all-member restore can still roll back; must identify and prove a separate irreversible bootstrap/continuity fact, independent verifier and privileged custody. A “quorum” label is not proof. | **Preferred review candidate**, contingent on a concrete tested R continuity and W recovery model; no vendor/technology choice. |
| **B — Non-exportable / monotonic hardware- or externally anchored root, plus ordered state service** | Potential independent sealed counter/signing-root epochs resistant to ordinary W backup rollback. | Monotonic counter does not by itself record OPEN/effects, distinguish cloned app credentials, solve physical replacement, availability or verifier downgrade; performance, custody and replacement may limit use. Claims need platform-specific assurance. | Parallel design alternative, **not** an HSM/TPM/KMS approval or a demonstrated fact. |
| **C — Append-only immutable/WORM audit checkpoints** | May preserve historical commitment evidence against deletion in a defined retention and administrative scope. | Does not alone deliver **linearizable latest-head**, atomic admission vs takeover, freshness or indefinitely surviving custody; new object versions can coexist with locked older versions, retention expires. | **Supplemental audit evidence only**, not an authorization root by itself. |
| **D — Permanent fail-closed quarantine after continuity loss** | Avoids authorizing a previous generation when proof is absent. | Potential indefinite outage; old live endpoints also require hard fencing and admission control to make a global pause credible. | **Required fallback** in every architecture, not proof of automated recovery. |

**Current decision:** retain **A** for independent review with **B** as a falsifiable root alternative, **C** solely as possible tamper-evident evidence and **D** as fail-closed fallback. Any preference changes after independent root-custody, durability, cost and failure-domain review. No provider selected.

## 4. Normative *candidate* invariants (none yet implemented/proven)

**G-INV-01 — Non-revivable epoch.** Once R's takeover to `B/e2` is durably acknowledged, every supported old-state restore, signer replay and C/W snapshot must deny `A/e1` *fresh* permits. If R itself is restored to a smaller `seq` without an independently preserved higher-head witness, **deny**; never mark restored epoch authoritative.

**G-INV-02 — Monotonic key and verifier policy.** Root identity, namespace, root incarnation, current signer-key epoch and minimum verifier manifest version are co-versioned with R head. An old private signer can never produce a **currently accepted** authorization merely because that key and trust store were restored together. Root rotation/rebootstrap without independent continuity proof is quarantined.

**G-INV-03 — Durable admission/OPEN before permit.** R serializes `ADMIT_OPEN(op, owner, epoch, actor, digest, tx_binding)` against `REVOKE_INTENT`; the durable OPEN becomes part of the authoritative committed R head before any valid first-use permit. Same idempotency key/digest returns same outcome; changed digest or altered holder rejects.

**G-INV-04 — No late COMMIT after successor READY.** An admitted old transaction remains in R's durable unresolved set from admission through a *positively witnessed* local durable COMMIT/ABORT, including loss of ACK, network partition or restart. `REVOKE_INTENT` stops new admissions/first uses but cannot silently close an existing hold. No successor live permit/READY while old authorized work **could still commit**. A post-hoc guard check alone does not close this interval.

**G-INV-05 — Root/W restore completeness.** W may serve permits only after independently authenticated R head comparison, full replay/integrity of every still-unresolved operation and active guard/actor admission. Missing historical OPEN or mismatched restored W ledger => `QUARANTINED`, not an empty safe ledger. Same head digest requires a complete state proof, not just one matching scalar counter.

**G-INV-06 — Physical actor and verification scope.** A restored app/guard with pre-R logic or copied actor credentials is not admitted merely because its SID/hostname matches. Separate manifest admission, quarantined SQL/issuer/pool paths, revocation and hard-fence are mandatory. **Physical same-identity clone safety remains unsupported** until genuinely independent actor identity/hard fencing is established.

**G-INV-07 — Unknown outcome stays blocked.** `OPEN_UNKNOWN`, `FENCED_UNRESOLVED`, W missing transaction history or unverified R remain deny states. No automatic or manual “release for progress”, TTL, inferred abort, signer-only receipt or fixture reset can grant successor authority.

## 5. State, linearization and crash boundaries

**State outline (proposed, not actual implementation):**

`ROOT_UNKNOWN -> ROOT_VERIFIED -> ACTOR_ADMITTED -> ACTIVE(owner/e)`

For each operation: `ADMIT_PENDING -> R_OPEN_COMMITTED -> FIRST_USE_VALIDATED -> IN_FLIGHT -> KNOWN_LOCAL_COMMIT|KNOWN_LOCAL_ABORT -> R_CLOSED_COMMITTED`

If local outcome cannot be proven: `IN_FLIGHT -> OPEN_UNKNOWN` (durable, **nonreleasable** in this design slice).

For takeover: `ACTIVE(A/e1) -> REVOKE_INTENT(A/e1) -> SUCCESSOR_RESERVED(B/e2) -> (all old holds known resolved / separately proven hard fenced) -> R_ACTIVATION_COMMITTED(B/e2) -> B_READY`.

**Linearization obligations:**
- R OPEN and R revoke intent have a **single total order**; no initial permit before R OPEN commit ACK. A lost OPEN ACK requires same-key lookup; no grant by guess.
- A current R status/first-use check is required even for permits signed before revoke. Already started work may complete while its hold remains; `B_READY` must wait.
- Closing requires positively known durable local effect and a recorded R close head. A lost local COMMIT, ABORT or R CLOSE ACK never allows guessing outcome or deleting a hold. Repeated close with a bound receipt must be idempotent and detect changed-intent replay.
- Multi-system R/W/local-DB transactions need a **specific atomicity or conservative blocking contract**. A crash between R and W updates or between local outcome and R CLOSE must not reopen authority. If coordination cannot prove the invariant, the intended result is indefinite BLOCKED, not availability.
- If prepared transactions are unsupported, `max_prepared_transactions=0` and actual operation path denial belong to the accepted implementation manifest. If later supported, all prepared transactions must be visible to R's hold/reconciliation model; disappearing sessions do not terminate them.

### Exact future crash and adversarial cuts (all unexecuted for real R)

| Cut / adversarial history | Required response |
|---|---|
| R head committed, W not yet updated; lost R ACK | W replays verified head or DENY; no second epoch guessed |
| W snapshot from epoch1 after R epoch2 commit | Old A cannot issue/read; restored W must QUARANTINE/replay complete current head |
| R rollback/rebootstrap old private signer + older verifier policy | Independent continuity detects stale root/policy or global DENY; **unproven** |
| R majority vs isolated minority, conflicting signed responses | No two current owners; minority/unknown-verifier clients DENY |
| Signed stale response arrives after REVOKE_INTENT | Fresh first-use/nonce/root-policy check DENY |
| Two copies share PG SID, key and actor ID | No assertion of safety without independent actor-incarnation identity or hard fence; mode BLOCKED |
| R OPEN committed, W/client/guard crashes before permit | OPEN remains recorded; same-idempotency retry or DENY |
| Local COMMIT is durable; COMMIT ACK lost; R CLOSE unknown | Hold remains OPEN_UNKNOWN; successor DENY (until separate safe outcome proof) |
| Local ROLLBACK/ABORT, ACK lost, W CLOSE reply lost | No assumed ABORT; explicit pre-ABORT and lost ABORT/CLOSE ACK tests still NOT_RUN |
| W/R restart while old local tx in flight | Holds persist or root enters DENY; never auto-clear after restart |
| R history/keys lost and no independent continuity witness | No authoritative recovery; indefinite freeze pending separate security decision |
| Unreachable R during ordinary authorization | Every new issuer/SQL/RLS permission DENY; observed existing reads cannot be retroactively revoked |

No **automatic** revival to `B_READY` is allowed merely because an R root identity can be regenerated.

## 6. Restore, root compromise and operations runbook (design only)

1. **Suspected W rollback or inconsistent R head:** quarantine W and all affected SQL/issuer/pool authorization, stop issuing fresh permits, preserve logs and state digests out of band. Do not trust a snapshot timestamp, PostgreSQL SID or signature alone.
2. **Independent R continuity check:** compare authenticated latest committed `seq/root/namespace/policy` against independently retained root policy and complete operation commitment. Any gap/conflict/signed stale history => DENY. An R restore is **not** self-authorizing.
3. **Actor hard-fence and admission:** revoke/disable old actor credentials on a genuinely independent control plane; enforce NOLOGIN/session drain and verified guard manifest for admitted supported restore modes. These steps do not by themselves prove already prepared/in-flight work aborted.
4. **State rebuild:** W replays and verifies its full operation ledger to the exact current R head, including OPEN_UNKNOWN; if impossible, stay quarantined. C/application logical restores must not lower the current R head or guard policy.
5. **Resume rule:** require independent evidence of current R root/policy, complete ledger replay, actor admission and no unresolved old work before successor READY. If unavailable, preserve fail-closed outage and escalate; no implicit emergency key reset, break-glass override or approval signature substitutes for proof.
6. **Root/credential compromise:** define a separate incident security contract and root-key retirement process before any operational recovery implementation. Without a surviving nonrollback witness, old signed authorization may be indistinguishable; **no automatic self-healing promise** is offered.

**Excluded in this R0 scope:** a malicious controller with unrestricted R + verifier-root control, malicious DB superuser bypassing SQL/RLS, cloud account takeover governing all independent roots, nonclonable physical identity without evidence, arbitrary external business side effects and a general orphan-clearing protocol. These exclusions must remain visible to the next reviewer and cannot be silently carried into Production.

## 7. Evidence plan and stop/go decisions

**Evidence inherited, NOT proof of R:** 129 original distinct GREEN in separate suites, 40 S0-09F distinct GREEN under `W_ORACLE_ASSUMED` with three mutation RED/GREEN receipts; original S0-09D C-only rollback **FAIL_SECURITY**.

**Mandatory independent design review of this R0 before any Lane2 experiment:** (a) identify R's *actual* nonrollback primitive and who controls its backup/custody, (b) verify latest-head freshness/completeness, (c) challenge total order of OPEN/revoke and local commit, (d) prove that restored verifiers and old private signers cannot bypass R, (e) determine whether two independently controlled physical W/root domains can be supported without hidden shared-admin trust, (f) document cost, availability and incident response limits.

**Proposed future limited experiments, all `NOT_RUN` until independently authorized:**
1. Current R vs actual W snapshot rollback `e2->e1`, with original legacy D security assertion *unchanged*, and a separately named R-backed issuance/RLS denial assertion. Deliberately disable fresh R verification in disposable fixture => controlled RED; restore exact SQL/ACL/policy and re-observe GREEN.
2. Restore R own snapshot, root namespace, previously retired signer and old verifier policies together; require actual independent nonrollback witness or **DENY/BLOCKED**, never mere “restored health” GREEN. If physical root control cannot be established, record `BLOCKED / NOT_RUN`, not a mock-driven PASS.
3. Real split-brain/minority/one-way network partition; lost CAS ACK, delayed valid signature, minority signer and dual B contenders; verify no concurrent live authorization or unknown -> ready transition.
4. Physical same-identity copy/PITR/standby promotion with copied actor keys and old guard; demonstrate full admission quarantine or document mode unsupported.
5. OPEN/admission/revocation/local COMMIT and ABORT through exact crash windows, including **pre-ABORT, lost ABORT and lost CLOSE ACK**, true transaction replacement, ordinary restart, and W/R head replay completeness.
6. Mutations that remove R current-head check, R OPEN durability, signer retirement or actor admission should each produce reason-specific RED (not vacuous denials); restore exact source and full inherited case inventory.

Do not claim a 169-test combined suite or transfer the F oracle's GREEN to a real R implementation. No new actual tests, PR or W-root code have been created by this architecture document.

### Decision gate

`R0_DESIGN_CANDIDATE_FOR_INDEPENDENT_REVIEW` **only**. No vendor/consensus/HSM/KMS selection, no W-root implementation approval, no safe orphan OPEN clearing, no protocol ratification, no Product/Production deploy. After independent read-only review of root feasibility and contract gaps, Astra Management must issue a separate **specific** decision for a bounded Lane2 implementation proof (if warranted). If a credible independent root cannot be specified, retain a **permanent fail-closed unsupported-recovery** classification.

[Architecture #23](https://github.com/alireza-anari/cac-project/issues/23) P0 OPEN, [baseline #9](https://github.com/alireza-anari/cac-project/issues/9) OPEN, [SOURCE-001 #1](https://github.com/alireza-anari/cac-project/issues/1) / GATE-SOURCE BLOCKED. Draft PRs #11/#16/#18/#20/#22/#24/#25/#27 remain open/unmerged. APR-033/034/035/036 unchanged; no historical source recovery, Production, onboarding or Sprint0 approval.

## 8. Primary technical references (context, not chosen technologies)

- [etcd v3.6 official disaster-recovery guide](https://etcd.io/docs/v3.6/op-guide/recovery/): a snapshot restore can move revisions backward and has special revision-bump/watch-invalidation semantics. A revision bump is **not** an independent CAC authorization key/epoch continuity proof.
- [PostgreSQL 17 PREPARE TRANSACTION](https://www.postgresql.org/docs/17/sql-prepare-transaction.html): prepared transactions persist beyond the initiating session and can later be completed by another session; they cannot be ignored in any supported “old tx cannot commit” invariant.
- [AWS S3 Object Lock official guide](https://docs.aws.amazon.com/AmazonS3/latest/userguide/object-lock.html): WORM protects versions under configured retention, but new versions can coexist. This is not a linearizable latest-head authority service, nor a CAC vendor selection.
- [NIST SP 800-57 Part 1 Revision 5](https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-57pt1r5.pdf): key lifecycle, revocation and compromised-key state inform the required explicit signer/trust-policy retirement contract. NIST guidance alone is not proof of an implementation.
