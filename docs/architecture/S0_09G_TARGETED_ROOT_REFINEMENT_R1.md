# CAC — S0-09G R1: Targeted Independent-Root Design Refinement

**Date:** 2026-11-06  
**Authority:** Astra Management / Architecture & Security  
**Tracking:** [Architecture Issue #28](https://github.com/alireza-anari/cac-project/issues/28); parent [#23](https://github.com/alireza-anari/cac-project/issues/23)  
**Parent architecture:** [R0](S0_09G_REAL_W_ROOT_DESIGN_CANDIDATE_R0.md), unchanged  
**Independent finding source:** [Draft review PR #29](https://github.com/alireza-anari/cac-project/pull/29), exact head `e63b16a0916aa6a43d5a36a20027dab20b506464`, [five P0 and three P1/one P2](https://github.com/alireza-anari/cac-project/blob/e63b16a0916aa6a43d5a36a20027dab20b506464/docs/security/S0_09G_ROOT_DESIGN_READ_ONLY_REVIEW.md)  
**Decision:** `TARGETED_DESIGN_REFINEMENT_R1_PROPOSED / REAL_LANE2_POC_NOT_AUTHORIZED / ALL_P0_SECURITY_PROOF_OPEN`  
**Scope:** documentation-only proposed architecture; no real R implementation, vendor selection, security certification, or code changes.

## Management decision

**Accept** the review's five P0 contract gaps (G-P0-01..05), P1 operational and proof gaps and P2 evidence vocabulary. **Retain the independent-root direction and refine its supported failure boundary**, rather than relabeling a restorable database “R” and repeating an assumed-oracle experiment.

R1 chooses one **falsifiable bounded design candidate**, not a Production topology: a majority-committed authority/operation log with independent *non-restored surviving quorum and mandatory trusted verifier admission*. The claim is limited to restoration of W and minority R members **while a previously admitted up-to-date R quorum and independent verification policy remain intact**. **Total R/root + verifier rollback is explicitly UNSUPPORTED** and no safe global denial can be claimed if every mandatory verifier/authorization boundary is also restored into obsolete permissive code. Whether that boundary can actually be enforced, including copied old endpoints, is itself P0 unproved.

Do **not** interpret this design as demonstrated nonrollback durability or safe recovery for catastrophic majority loss, privileged R compromise, physical cloned root identity or general orphan resolution.

## G-P0-01 — Name a terminal continuity primitive and exact recovery budget

### Bounded candidate Q: non-restored quorum commit as the surviving fact

- In the experimental candidate, `R` is one namespace state machine replicated over an **odd voting set, proposed five participants; a write commits only after durable majority acknowledgement of its log entry**, with validated leader term/configuration and a read that establishes a current majority read-index or equivalent linearizable read. Every log entry includes explicit preceding commitment and configuration revision; no member may invent an acknowledged prior sequence.
- **The actual surviving fact for the scoped restore** is the committed log prefix and current configuration held by at least **three previously admitted, non-restored voting members**. An old snapshot of W or of one/two minority R members cannot override that surviving majority. A single leader's signature, new node ID, mere quorum size or unverified revision-bump is insufficient.
- The admitted quorum must **not share the same recoverable backup/restore authority** as W/A/B/C; the operative independence and access-control matrix, durability/backup practices and member replacement are **deployment assumptions to measure**, not facts established by this document. A privileged actor able to roll back/replace a majority and its current verifier policy defeats the candidate and is outside its narrow supported envelope.
- Member admission/removal or policy/key change requires a *currently committed R configuration transition under the existing surviving quorum*, with authenticated old-to-new configuration continuity. An isolated restored minority cannot independently rebootstrap the same namespace. Old keys/old membership policy do not establish current status from a minority.
- If **three voting members' current committed history is lost**, membership/custody continuity cannot be verified, or W and the verifier cannot contact the admitted quorum, the only authorized response under an intact mandatory guard is `ROOT_UNVERIFIED / QUARANTINED / DENY`. There is **no** automatic service recovery, genesis reset, new namespace claiming old identity or emergency leader election from an old snapshot. A fresh independently governed trust-root ceremony is a *separate unapproved architecture decision*.
- A restored R member may rejoin only as a **non-voting quarantined learner** against a currently admitted quorum; it must obtain current identity, full committed log including unresolved OPEN and a new authorization to vote. It may not publish an earlier signed authorization during its resync. Destructive local restore outside this envelope is NOT_SUPPORTED.

**Alternative B:** a separately governed externally protected monotonic **state-digest/sequence root** combined with an authenticated complete ordered log, not a bare hardware counter, could replace the quorum-survival assumption *only* if a concrete physical primitive proves nonreset/nonclone, atomic state binding and independently current verifier policy across the selected restore envelope. Such a device/service is **not selected or approved**. B may supplement Q; neither a marketing HSM label nor Object Lock proves the required semantics.

**Cost/availability consequences:** Q requires physically/administratively separated voting custody and consistently accessible majority to authorize. Separate secure key/root rotation, replication cost, per-operation latency, queueing, replay storage, backup, decommission and incident drills are material unknowns; no numeric performance, RPO/RTO, per-transaction price, uptime or cost is asserted. Majority unavailable => all new permissions DENY; unresolved work can block takeover indefinitely.

## G-P0-02 — Root identity, verifier bootstrap and signer retirement

**Supported installation and operator manifest** (candidate): `root_genesis_digest, namespace, committed_membership_config, verifier_min_build_and_SQL_guard_fingerprint, approved_manifest_version, allowed_signer_epoch, trusted_endpoint_set, actor_incarnation_policy`. This manifest and the **ability to enforce it at every authorization path** must be governed outside the W/A/B/C restore scope.

1. **Genesis:** a distinct, audited enrollment ceremony pins R's initial namespace/root digest and admits independent verifier/guard versions and actor identities. It **does not** bootstrap from a recovered W/C key, R snapshot timestamp, IP address or PG system ID alone.
2. **Current trust:** the guard, issuer and reused PgBouncer/RLS entry points verify a **fresh current majority-backed R decision and the latest approved signer/verifier policy** before honoring new use, not merely validate a locally cached signature. Restored C-only/pre-R guards are **quarantined at the network/DB authority boundary before they can issue or query data**. A deny-only new service is insufficient if an old SQL/issuer path can still bypass it.
3. **Key and policy retirement:** R commits `retire signer epoch` and minimum accepted manifest as an ordered entry; new admission rejects old signers even if their private keys were restored. Old-key responses and stale signed certificates cannot be accepted by an independently updated verifier. Copied old actor credentials and physical same-SID clones are **NOT_SUPPORTED** without independent actor-instance enrollment and demonstrable hard exclusion.
4. **No hidden self-admission:** current software cannot certify its own build hash, automatically lower policy on failure or re-enroll a prior verifier from restored state. Member, verifier and actor re-enrollment each require externally authenticated current policy; a member identity is distinct from application physical actor identity.
5. **Trust boundary:** an administrator controlling both the R quorum history and the mandatory verifier/guard enforcement can violate the premises. Formal proof of separation, key custody and all old-endpoint exclusion is a **P0 operational proof obligation**, not established by R1.

If verifier enforcement outside the restore domain is unavailable, **do not claim fail-closed old-verifier restoration**; that restore mode is unsupported.

## G-P0-03 — One authoritative commit for head + OPEN + journal completeness

**Reject the original loose separation of an R scalar head from a W-only operation journal.** For this candidate, the R **majority-committed replicated state-machine log itself is the authoritative complete operation journal**. Every state-changing record must be in one ordered namespace log; no separate “R head committed / OPEN only in W” success path is allowed.

A log entry contains a `namespace, committed_term/index, prior_entry_digest, operation_id, idempotency_key_and_intent_digest, owner_epoch, actor_incarnation, local_db_and_tx_binding, command, resulting_head_digest, OPEN_state_or_close_evidence_ref, signer_policy_version`; its deterministic state transition updates head/owner/revoke/OPEN status in the **same committed log index**. Permit delivery happens **after** the relevant log entry's majority durable commit and an admitted guard has authenticated the decision.

- `ADMIT_OPEN` atomically records an OPEN hold, exact operation identity/digest and current owner/epoch in the committed R log before any permission to start local work.
- `REVOKE_INTENT` is totally ordered against `ADMIT_OPEN` and `FIRST_USE` and blocks all later old-owner first uses/admissions. Earlier IN_FLIGHT operations retain holds until trusted outcome is known.
- `CLOSE_KNOWN_COMMIT/ABORT` may append only when **positive, durable, transaction-specific and DB-incarnation-specific outcome evidence** has been obtained from an approved independent path. A lost COMMIT/ABORT ACK, client timeout, old W snapshot, disappeared backend or operator approval alone does not suffice. Repeated same-key/evidence CLOSE may return committed status; changed evidence/digest must reject.
- `OPEN_UNKNOWN` persists across member changes, snapshots and ordinary restart and is not garbage-collected, auto-closed or converted to a “safe aborted” record.

**Replay/compaction rule:** a checkpoint is usable only if it includes a verifiable **complete pending-OPEN set, owner/policy and idempotency/tombstone state** at the exact committed prefix, with a cryptographically authenticated prefix/head digest and a contiguous retained suffix. Compaction may not erase unresolved holds or the records required to prove them. Recovered W with mismatched head, missing entries or ambiguous state goes `QUARANTINED`; it may not infer an empty OPEN set.

**Crash/ACK matrix:** after R accepts but before client ACK, the caller may retry only with the original idempotency key and request digest, checking the currently committed log; unknown => DENY. If majority commit is uncertain, no permit is issued on an unverified response. After local commit but before R CLOSE, the operation remains OPEN_UNKNOWN and blocks successor. When member snapshot restore lacks the log prefix and cannot verify complete replay, no authorization. Exact durable commit/ACK storage ordering is **to be proven experimentally**, not assumed because the API says “quorum”.

## G-P0-04 — First-use and revoke ordering: state the promise honestly

**Chosen safety semantics: prevent new first uses after serialized revoke; never declare successor READY while earlier admitted transactions may still commit.** Do **not** claim that revoking R can instantaneously cancel a transaction already running in PostgreSQL. A fresh signed nonce or an R status check made *before* a network round trip is not a physical instantaneous kill switch.

Candidate transitions under the **one R ordered log**:

`ADMIT_OPEN(e,op) -> FIRST_USE_GRANTED(e,op) -> LOCAL_TX_IN_FLIGHT -> (KNOWN_COMMIT|KNOWN_ABORT|OPEN_UNKNOWN) -> CLOSE_PROVEN`

versus `REVOKE_INTENT(e)`:
- `FIRST_USE_GRANTED` is an R-logged, durable single-use transition, **authorized only while not REVOKING**, tied to an exact operation, actor and *already identified local DB transaction*.
- An old delayed first-use response cannot authorize a **new** local transaction after a revoke. Enforce use-once transaction binding via the current guard; permit delivery without transaction identity or trusted active admission is not an authorization.
- **Race rule:** if the grant precedes revoke in R's total order, the local transaction may already be in flight, including after the revoke is recorded; its **OPEN hold still blocks `SUCCESSOR_READY`** until a positively known durable close. If revoke precedes grant, grant is denied.
- In-flight old work may commit after revoke while successor is still NOT_READY. This is the chosen weaker but explicit invariant. If the application requires zero old writes after revoke, that is a **different design requiring real physical hard-fencing/transaction cancellation**; it is not claimed here.
- If a grant is committed but the local use/response is delayed or abandoned, the hold remains unresolved. Even if the old actor was physically isolated, do not infer local ABORT without verified outcome/effect evidence. Local guard authorization, DB session-reuse binding and actual local COMMIT scheduling require dedicated PoC cuts.
- A stale, pre-R or unsupported physical clone actor cannot become admitted merely by replaying a prior grant or matching PID/fullxid; effective SQL/ACL/RLS enforcement and independent root identity remain mandatory.

**Safety invariant:** at no instant may `SUCCESSOR_READY(e+1)` and an `IN_FLIGHT / OPEN_UNKNOWN(e)` old operation that might still durably commit be simultaneously authorized. The **total R grant/revoke order** is a logical-order contract; testing actual local transaction start/COMMIT ordering and guard enforcement remains required.

## G-P0-05 — Hard fence does not settle UNKNOWN; Lane3 remains prohibited

Remove any interpretation of R0's alternative `all holds known resolved / separately proven hard fenced` as two equally sufficient conditions. **For Lane2, hard fencing is necessary for certain revocation scenarios but never, by itself, permits successor READY when effect outcome is unknown.** A physical actor disablement cannot undo a previously durable local COMMIT or prove all external side effects.

The only Lane2-authorized transition to successor readiness is after **every old operation has a positively verified, durably logged `CLOSE_KNOWN_COMMIT` or `CLOSE_KNOWN_ABORT`** and current R/verifier/actor continuity is proven. If any old record is `OPEN_UNKNOWN` or `FENCED_UNRESOLVED`, the namespace stays `BLOCKED`, even with administrator approval, old actor off, credential revocation, elapsed time or absence of a session.

There is **no** `OPEN_UNKNOWN -> CLOSED` exception in Lane2. Such recovery would be a separate, independently reviewed **Lane3** effect-reconciliation and externally witnessed outcome contract, currently `BLOCKED / NOT_RUN`. Fixture reset is allowed only to isolate tests and cannot be described as operational clearance.

## P1 refinements, cost envelope and security-test requirements

- **G-P1-01 custody/failure/cost:** require a role/authority matrix for independent voting members, backups, root/manifest enrollment, signer retirement, member replacement and restore. Specify common cloud-account/operator/controller parent, blast radius and allowed faulty members. A and B alternatives evaluated against majority loss, complete root loss, availability under partition, capacity/latency journal costs, retention, physical replacement and emergency on-call; remain unpriced and unselected. A design that cannot actually enforce non-restored quorum cannot claim Q's property.
- **G-P1-02 live enforcement/quarantine:** audit real entry points: direct issuer, SQL guard/RLS, PgBouncer backend reuse and old/physically cloned endpoints. A merely new verifier running elsewhere while old pooled sessions still access data fails the contract. SQL superuser/root bypass is excluded explicitly, not asserted protected.
- **G-P1-03 falsifiable controls:** before each negative test, prove current positive scoped authorization with a valid admitted contender/operation. Then apply a real fault or targeted weakening of *one control*, require the specific expected assertion RED for weakening or GREEN denial for live outage; restore byte-identical executable SQL/ACL/manifest and rerun. No mock-induced quorum/physical-root security claim. Preserve final-head Push+PR CI and independent review if ever authorized.
- **G-P2-01 evidence versioning:** separate `DESIGN_SPECIFIED` from `SECURITY_PROVEN` and `NOT_RUN`. Each claim must pin root/member/config and software/firmware versions, role/custody scope, failure envelope and exact evidence run IDs. 129 inherited + 40 new = **169 distinct prior GREEN cases across different suites**, *not* one combined 169-case job; original D `FAIL_SECURITY` is separate and unchanged. No new R tests exist.

### Explicit proof obligations before another architecture vote

1. Independently review whether quorum Q is a **credible terminal surviving fact** under a testable W/minority-R restore boundary, not silently assuming production protection against all-member root rollback.
2. Document exact permitted R voting-member loss/replacement and root/manifest control/backup authority; prove no old member/minority/retired signer can answer with current admission during these operations.
3. Show how a current independent verifier/guard is **actually mandatory** for every SQL/issuer/pooled route; absent that, STOP and redesign. Do not claim safety against jointly restored old verifier and W merely through a new control that old code bypasses.
4. Validate that journal/OPEN state is included atomically at the committed R log index, with replay completeness and lost-ACK behavior; no scalar-counter-only resume.
5. Execute ordered first-use/revoke versus actual local commit scheduling only after scope-specific permission, including crash prior to ABORT and lost ABORT/CLOSE ACK; old hold conservatively remains active.
6. Explicitly test the original unchanged D rollback as legacy `FAIL_SECURITY`; use separate named R/W path with a healthy current-root positive, controlled removal-of-root-check RED, restore and fresh GREEN, *never* relabel old RED as safe.
7. Lane3 orphan release, physical same-ID clone admission, R majority-total-loss automatic recovery, root/key custody certification, Production/IdP/onboarding and full HA/PITR remain outside this approval.

## Current gate and proposed next step

**Refinement verdict:** the five gaps now have **clear candidate contracts and a narrowed supported restore envelope for review**; none is empirically discharged. This is **not** `READY_TO_IMPLEMENT_LANE2` or even automatic `READY_TO_REQUEST_LANE2`. Request a **separate read-only R1 delta review**, specifically challenging (1) majority survival vs root restore assumptions, (2) all-endpoint verifier admission, (3) journal/head atomicity and replay, (4) first-use timing, and (5) irreversible UNKNOWN block. The review may recommend whether **a test-scoped W/minority-R restore PoC under the Q assumptions** is a defensible *request*. It must **not** claim general R own-rollback safety or an anti-rollback Production root.

All real R experiments `NOT_RUN`; historical S0-09D C rollback `FAIL_SECURITY`; S0-09F W oracle conditional. [Issue #28](https://github.com/alireza-anari/cac-project/issues/28) and parent [#23](https://github.com/alireza-anari/cac-project/issues/23) remain P0 OPEN; [baseline #9](https://github.com/alireza-anari/cac-project/issues/9) OPEN; [SOURCE-001 #1](https://github.com/alireza-anari/cac-project/issues/1) / GATE-SOURCE BLOCKED; Draft PRs #11/#16/#18/#20/#22/#24/#25/#27/#29 open/unmerged. `NEW_IMPLEMENTATION_EXPERIMENTAL / PROTOCOL_PROPOSED`, no Merge, vendor, Production, identity/onboarding, APR changes or Sprint0 acceptance.
