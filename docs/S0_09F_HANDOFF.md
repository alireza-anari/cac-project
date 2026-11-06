# S0-09F — assumed-W deny-only integration evidence

**W_ORACLE_ASSUMED / LANE1_ONLY / ROOT_AND_ORPHAN_RECOVERY_UNPROVED**

Result: **INTEGRATION_PROVEN_ONLY_UNDER_ASSUMED_W**, bounded to the executed fixture schedules. Stage3 source head `168543a32a937c56113c1b51b26b2fb82af17257` passed all40 new methods before/after the three restored security mutations in real Push/PR CI. Final report-commit CI will be separately receipted on Issue26/PR27 after that commit completes its checks; no self-referential commit SHA is embedded here. This document is not a production or protocol approval. SOURCE-001/GATE-SOURCE remain BLOCKED; Architecture Gate #9 and architecture Issue #23 remain OPEN. Legacy D rollback remains **FAIL_SECURITY**.

## Authority and source lineage

Execution [Issue26](https://github.com/alireza-anari/cac-project/issues/26), stacked [Draft PR27](https://github.com/alireza-anari/cac-project/pull/27), branch `work/s0-09f-w-oracle-deny-only-poc`, base `work/s0-09d-fencing-proof-gaps`. Exact inherited parent: `ca043e2751ea1dbcb7aed3c1ed3d171a9bb1f0e2` (Draft22). Authorization read at management main `03232f6753de98d8dc6b063920549e4db369366f`: `docs/architecture/S0_09E_LANE1_SCOPED_AUTHORIZATION.md`. R1 read at `29709ad3cb15380653deb7b1c1c52e88725d2a92`; accepted independent R1 review read at Draft25 `d10ced56dcd7a267a18fd5620ccc8c16a1856604`. Those documentation PRs were not merged/imported as ancestry.

Only the new `experimental/backend/w_oracle` package executes F behavior. Existing backend source/tests, including the original D rollback assertion, remain byte-identical to the parent. Two existing workflow files add branch/docs routing only; their security commands stay unchanged. The F workflow checks the inherited backend diff and current head/synthetic-merge source trees and emits a source receipt.

## Explicit trust model

W is a fourth disposable PostgreSQL cluster on the **same CI host**, with assumed current authenticated root/namespace/policy, serialized monotonic state, consistent online reads, independently retained durable OPEN and a trusted return channel. Independence here means separate PostgreSQL cluster system identifiers and exclusion from A/B/C logical schema restore, not independent disaster domain or irreversible storage. W signs/verifies in W; its signing material is never installed in app/C dumps. The trusted fixture controller also retains generated historical key values in its private configuration solely for evidence redaction; this is not a custody/isolation proof. Online signature re-verification occurs in W. Nonce/transcript checks are exercised; production TLS, key custody, root nonrollbackability and noncloneable identity are not proved.

The synthetic coordinator and external admission controller are trusted. Runtime/issuer use nonowner, non-superuser, non-BYPASSRLS roles; local SQL has only its W checker credential. Only the trusted coordinator can ADMIT/hold/CLOSE. It observes the connection it owns and acknowledges exact local transaction outcome; a SQL checker cannot close or invent outcomes. A DB superuser, host administrator, malicious controller/coordinator or compromised assumed W root can bypass this model and are excluded.

Current local guards are measured at runtime using catalog definitions, owners, effective ACL source, RLS/policies, relevant role powers and memberships. Admission independently executes the controller-owned catalog query; it does not trust the restored measurement function's result. Before supported app restore/reapply, the controller unadmits the actor, commits NOLOGIN, terminates and drains direct/pooled role sessions, then performs DDL. It compares an externally retained approved manifest, rotates the actor incarnation and only then readmits. A restored pre-W verifier stays quarantined. This is a trusted operational boundary, not physical attestation or self-protection of an obsolete verifier.

## Ordering and interface

`reserve(expected_epoch, request)` serializes CAS, rejects historical request reuse and all OPEN/UNKNOWN; reserved successor stays NOT_READY. Local C reservation/apply must commit, fresh-loopback committed ACK must confirm, local readiness/epoch binding must commit, and W activation must complete before readiness. C remains an additional deny-only dependency and can reduce availability; it cannot authorize around W.

`admit` binds root-domain/namespace/policy, current owner/epoch, actor/incarnation, manifest, operation ID, idempotency key, exact intent digest, role, local SID/PID/fullxid and W holder identity. Same request returns its original ticket; changing the intent fails, and another connection cannot rebind the original holder. ADMIT's transaction must commit and its ACK arrive before hold/first app use. A new local fullxid cannot reuse the ticket. Fresh guard-generated nonces and complete response binding protect the tested SQL paths.

The coordinator holds a W advisory transaction lock while its durable OPEN remains recorded. It also holds the inherited C fence. SQL challenge, issuer, context verification/RLS and final pre-COMMIT checks all require online W; no app C-only fallback is exposed. Revocation intent stops new admission/first use, but an already validated transaction may still commit while OPEN excludes takeover. This is not instant revocation of every in-flight transaction.

Release order is **known local durable COMMIT/ABORT ACK → C.finish COMMIT → W.close COMMIT**. CLOSE locks its operation row before checking, so UNKNOWN cannot be overwritten by a racing CLOSE. No timeout, missing-session heuristic, manual release or successor authorization clears unresolved OPEN.

An INTRANS exception can close as ABORT only after exact transaction binding is rechecked and ROLLBACK is acknowledged. In INERROR, SQL cannot confirm the original fullxid; even after rollback the implementation conservatively retains UNKNOWN. Hostile COMMIT/BEGIN replacement also retains UNKNOWN. Real query cancellation/division-by-zero therefore cause a deliberate availability block. No orphan recovery is implemented or authorized.

## Test inventory and falsifiable claims

The previous 129 distinct GREEN inventory is **94 full backend +20 C +15 D**, in separate applicable workflows. Repeated before/after runs do not increase distinct counts. The additional legacy D rollback assertion remains a separate real unsafe assertion RED, not a passing security case. F counts are 15 API +11 SQL/integration/pool +14 fault methods = **40 distinct new methods**, all executed; one method covers nine crash cuts. Mutation probes rerun existing methods and do not add distinct tests.

| Claim / attack | Actual mechanism | Observed result |
|---|---|---|
| API CAS / OPEN / role separation / digest idempotency / restart | Real W PostgreSQL, independent checker/coordinator sessions, Docker restart | PASS: 15 API methods at Stage3, including no holder rebinding |
| CLOSE versus concurrent UNKNOWN | Actual observed row-lock wait and two coordinator connections | Real assertion RED at `5fe69f5`; same assertion GREEN after row lock at `0f84216` |
| SQL/issuer/RLS mandatory W | Positive scoped read; raw nonowner negative entry points; private C-only originals inaccessible | Stage2 PASS |
| C rollback while W current | Actual C pg_dump/pg_restore epoch2→1 after B takeover, W remains epoch2/B | Stage2 PASS; old A readiness/issuance/SQL/RLS denied |
| Supported A→B app restore | Actual independent cluster dump/restore, current guard admission, new actor incarnation | Stage2 PASS |
| Old pre-W verifier | Quarantine, remove overlay, external manifest rejection, NOLOGIN retained | Stage2 PASS; no old verifier admitted |
| Overlay rollback/reapply / ACL/RLS | Reversible overlay, exact structural catalog hash and positive reactivation | Stage2 PASS |
| COMMIT pool backend reuse / takeover | Real PgBouncer size1; same PID/new fullxid; old token/C-ticket/W-ticket | Stage2 PASS |
| ROLLBACK / actual cancellation pool reuse | Division-by-zero and observed PgSleep + pg_cancel_backend; same PID/new fullxid | Stage2 PASS denial; UNKNOWN and successor BLOCKED |
| Known exact ABORT / transaction replacement | INTRANS exact binding plus rollback ACK; COMMIT/BEGIN + exception negative | Stage2 PASS; replacement never closed as original ABORT |
| OPEN through final guard and local commit | Independent W observer and rival reservation before permit, after guard, after COMMIT ACK | PASS at Stage3; eligible admitted B confirmed before rival denial, CLOSE only last |
| Crash cuts / W restart / lost ACKs | Real child os._exit77 and loopback PG-wire faults | PASS in Stage3 Push/PR (scope below) |
| W outage / partial channel refusal / stale response / identity faults | Actual process stop; refused checker connection; old real signed proof; config/actor mismatch | PASS in Stage3 Push/PR (scope below) |
| Paired takeover / concurrent local transactions | Two-thread barriers, actual W CAS and independently bound local transactions | PASS in Stage3 Push/PR (scope below) |
| W CAS / OPEN / mandatory SQL sensitivity | Three temporary SQL mutations; one intended assertion RED, exact restore, same probe GREEN | PASS in Stage3 Push/PR (scope below) |
| Prepared transactions | Actual PREPARE rejection and empty pg_prepared_xacts | PASS in Stage3 Push/PR (scope below) |
| W rollback/root recovery / rebootstrap / physical same-identity clone | Forbidden Lane2; no implementation or experiment | BLOCKED / NOT_RUN |
| Orphan reconciliation / timeout/manual clearing / unknown successor | Forbidden Lane3; no implementation or experiment | BLOCKED / NOT_RUN |
| Production HA, network partition matrix, power-loss/disk corruption, Byzantine W/host | Outside authorization and fixture capabilities | NOT_RUN |

## Stage commits and CI receipts

All links below refer to actual executions, not requested dispatches. Full run conclusions and decoded logs are checked separately from the legacy security classification.

| Stage | Exact head | F Push | F PR synthetic merge | Observation |
|---|---|---|---|---|
| Test-first scaffold | `8f81bea5796dd0da8a97662efa0972a9431e4d10` | [42190816105](https://github.com/alireza-anari/cac-project/actions/runs/42190816105) | [42190820706](https://github.com/alireza-anari/cac-project/actions/runs/42190820706) | Missing reserve API; development error, not security sensitivity |
| API candidate | `aaf89ba18f0bf49e1c4ba6a80b3c702ad963ce7e` | [42192046466](https://github.com/alireza-anari/cac-project/actions/runs/42192046466) | [42192053214](https://github.com/alireza-anari/cac-project/actions/runs/42192053214) | 10 API tests PASS; review subsequently found lifecycle race |
| Real race regression | `5fe69f5636033739e0b9c2acd6775d01f3b7c917` | [42193663094](https://github.com/alireza-anari/cac-project/actions/runs/42193663094) | [42193670186](https://github.com/alireza-anari/cac-project/actions/runs/42193670186) | Intended real assertion FAIL: CLOSED instead of DENIED |
| Stage1 corrected | `0f842161effd1c033cb3634b3398a92130f074f1` | [42193880340](https://github.com/alireza-anari/cac-project/actions/runs/42193880340) | [42193886361](https://github.com/alireza-anari/cac-project/actions/runs/42193886361) | 14 PASS; all inherited workflows PASS on same head |
| Integration test-first | `e93f2eec28ea7750174534897c40300be1c725ca` | [42195419360](https://github.com/alireza-anari/cac-project/actions/runs/42195419360) | [42195425727](https://github.com/alireza-anari/cac-project/actions/runs/42195425727) | Missing integration module; development error |
| Stage2 corrected | `7f6652574ddb726f49a5236d5f986a64c8e5984c` | [42196141325](https://github.com/alireza-anari/cac-project/actions/runs/42196141325) | [42196150321](https://github.com/alireza-anari/cac-project/actions/runs/42196150321) | 25 PASS at that checkpoint; strengthened/superseded by Stage3 |
| Stage3 corrected | `168543a32a937c56113c1b51b26b2fb82af17257` | [42199153251](https://github.com/alireza-anari/cac-project/actions/runs/42199153251) | [42199159766](https://github.com/alireza-anari/cac-project/actions/runs/42199159766) | 40 PASS twice; all 3 EXPECTED_MUTATION_RED + exact restore + same probe GREEN |

Stage3 candidate observations: `25e555f` Push42198164352/PR42198172466 reached the prepared-transaction case: PostgreSQL refused PREPARE, but cleanup deliberately surfaced FenceDenied, so the outer SQLSTATE-capture assertion was misplaced. `ca6603a` Push42198736396/PR42198744105 then correctly rejected an RLS positive setup using an uncommitted issuer ledger; corrected helper first commits legitimate issuance before opening the live issuer fault probe. Neither setup error is a passing security RED or a relaxed control. Corrected candidate `168543a` completed 40 methods twice, all 3 intended mutation RED/restored GREEN in both Push/PR.

Stage3 `9e07ea6` Push42197654645/PR42197662187 failed the delayed-revoke expected-state assertion because B was unadmitted, so the intended transition never ran. Correction `25e555f` actually restores/admit B and positively checks W status before contender denials. The stronger Stage3 rerun passed the corrected eligible-contender probes; earlier Stage2 reason-specific OPEN claims rely on this later evidence; this is not a claim of a successful revoke or accepted bypass.

Development failures are retained honestly: `dd1baae` failed schema parsing (CASE delimiter); `e24d14b` failed wrapper installation permissions. Fixes used correct parser boundaries and migrator-created wrappers with explicit NOLOGIN guard ownership. No role gained CREATE/BYPASSRLS and no assertion was relaxed to pass these failures.

Stage1 regression receipts: full94 [Push42193880253](https://github.com/alireza-anari/cac-project/actions/runs/42193880253) / [PR42193886172](https://github.com/alireza-anari/cac-project/actions/runs/42193886172), C20 [PR42193886432](https://github.com/alireza-anari/cac-project/actions/runs/42193886432), D15 + legacy unsafe rollback [Push42193880229](https://github.com/alireza-anari/cac-project/actions/runs/42193880229) / [PR42193886165](https://github.com/alireza-anari/cac-project/actions/runs/42193886165), focused B [PR42193886234](https://github.com/alireza-anari/cac-project/actions/runs/42193886234). All completed SUCCESS as workflows; D's security rollback explicitly remains FAIL_SECURITY/BLOCKED.



Stage3 all-eight-workflow checkpoint on `168543a32a937c56113c1b51b26b2fb82af17257`: full94 [Push42199153484](https://github.com/alireza-anari/cac-project/actions/runs/42199153484) / [PR42199159830](https://github.com/alireza-anari/cac-project/actions/runs/42199159830), C20 [PR42199159800](https://github.com/alireza-anari/cac-project/actions/runs/42199159800), D15 + legacy FAIL_SECURITY [Push42199153011](https://github.com/alireza-anari/cac-project/actions/runs/42199153011) / [PR42199159769](https://github.com/alireza-anari/cac-project/actions/runs/42199159769), focused B [PR42199159839](https://github.com/alireza-anari/cac-project/actions/runs/42199159839). All completed SUCCESS as workflows, preserving the separate unsafe legacy rollback classification. Exact final documentation-head Push/PR checks remain pending at document creation and **will** be separately receipted in Issue26/PR27 after completion. Executable source is unchanged by the report commit.

### Stage3 artifact/source receipts and actual observations

| Event | Artifact ID | Verified ZIP SHA256 | Tested revision |
|---|---|---|---|
| Push42199153251 | 13493089210 | `b079dc2e807813032c5eafd18552e7f77b0c3c4410ca336004008af86b61214f` | `168543a32a937c56113c1b51b26b2fb82af17257` |
| PR42199159766 | 13492713468 | `720af6c2370eb503dfb4e1c2cf0d523d7808668df468a89b6d086c7bb342bc65` | synthetic `8c9a1c79b04b0e4a9125cbb98fc5bcf1332c11f3` |

PR head is `168543a32a937c56113c1b51b26b2fb82af17257`; Push/head/synthetic all record F source tree `367218ab9f1b287f3fb7f4ce615bc068415018bc`. CI also rejects any inherited backend source diff versus the parent. Nine downloaded files: `oracle-bootstrap.log`, `proof.log`, `post-sensitivity.log`, `sensitivity.log`, `topology.log`, `pool-versions.log`, `source-receipt.log`, `tested-sha.txt`, `pr-head-sha.txt`. No private configs/dumps are included.

PR topology witnesses: A `7704995993681539110`, B `7704995996641415206`, C `7704996000647995430`, W `7704996003246583845`. All four are distinct. Inherited ABC loopback HBA trust entries are explicitly logged; this is disposable trusted-host infrastructure, not a production HBA/TLS/host-isolation proof.

Pool PR witnesses: commit PID1441 fullxid1454→1459→1461; actual cancellation PID1411 fullxid1433→1438→1440; rollback PID1478 fullxid1475→1480→1482. Before/after takeover or blocked takeover, old context/tickets never yielded an unauthorized read. These observations do not attribute denial solely to fullxid; independent API hold tests separately vary transaction bindings.

Nine actual unresolved crash/restart cuts: after durable OPEN ACK; before first app use; after first app use; after final guard; before local COMMIT; after local COMMIT before CLOSE; after known local ABORT before CLOSE; after C.finish COMMIT before W.close; after W.close executes before its COMMIT. Each retains OPEN/UNKNOWN across ordinary W restart and excludes an admitted contender. Additional actual process cuts before OPEN COMMIT show no permit/history granted; after acknowledged CLOSE permits safe new epoch. Worker exit77 is checked and requested cut receipts must be present.

Two loopback PG-wire faults intercept actual `CommandComplete COMMIT`: loss of W OPEN COMMIT reply retains committed OPEN and returns no permit; loss of local issuer COMMIT reply independently observes the committed ledger effect while retaining UNKNOWN. Ordinary W restart preserves these holds. This is actual wire loss, not just a hook pretending an ACK was lost. Wire loss of CLOSE ACK, disk/power loss, physical restore and arbitrary packet schedules are NOT_RUN.

Valid live issuer arguments/ticket and a runtime context with an already committed ledger succeed before checker-channel refusal, real W outage, stale signed response, root/namespace/policy/incarnation or actor mismatch. The exact same live SQL paths then return42501. Faults are restored before connection cleanup; unresolved outcomes remain excluded. C's extra dependency can keep current B NOT_READY after C rollback: the experiment establishes denial, not automatic availability recovery.

| Mutation | Intended RED assertion | Exact restored catalog SHA256 | Restored result |
|---|---|---|---|
| W_CAS | stale expected epoch was accepted (InsufficientPrivilege not raised) | `cc18856c896dfccd693544ef16aac3674637e58ae1b1aa0f51116306826655ac` | same probe GREEN |
| W_OPEN | orphan OPEN no longer excluded reservation | `cc18856c896dfccd693544ef16aac3674637e58ae1b1aa0f51116306826655ac` | same probe GREEN |
| W_SQL_ENFORCEMENT | old A actually newly issued/scoped-read under C1/W2, then old-authority denial assertion failed | `9db62aa80a86366eef1a573b3b550dfdf5127d5aa3cd0fb36b8a7983b48ef226` | same real C rollback probe GREEN |

Each mutant run requires exactly one intended assertion failure, zero errors/skips; restoration checks function definition, owner, ACL, SECURITY DEFINER and settings **before** any later fixture reset. Fresh namespace reset is independent test genesis, never operational OPEN recovery. Full40 then runs GREEN again. The injected unsafe bypass is a negative sensitivity witness, never an admitted fallback.

## Versions, reproduction and evidence limits

Actions Ubuntu24.04; Python3.12.15; hash-locked binary wheels. PostgreSQL **17.11**, image `postgres@sha256:839fbb5a4942a7758dd93e18b42ea5649807491a0545b5eeeb8f0b8bb11857a5`; PgBouncer **1.22.0**, Ubuntu package `1.22.0-1build4`. W asserts fsync/synchronous_commit/full_page_writes ON and max_prepared_transactions0. Four clusters use separate data directories/system identifiers, same host. The wire-loss proxy intentionally disables TLS only on a loopback synthetic connection; it records no wire payload or credentials.

Reproduce through `.github/workflows/w-oracle.yml` on the exact branch/PR. Bootstrap A/B/C then W with fresh synthetic credentials in private mode0600 files. Run `python -m w_oracle.run`, `python -m w_oracle.sensitivity`, then the full new suite again. Original independent full/C/D workflows supply the 129 floor. Local Docker/PostgreSQL were unavailable in this session: local AST/diff checks were not reported as database evidence.

Only allowlisted F evidence is uploaded, with W_ORACLE_ASSUMED banner, known synthetic credentials/proofs and all generated historical W signing keys scanned. Configs/private schema dumps are never uploaded and are removed. GitHub job logs are decoded/read as evidence, and both Stage3 F artifact ZIPs were downloaded and checked against their advertised SHA256 digests; nine explicit evidence files, banners, tested SHA and source trees were verified. Final report-commit artifacts/CI will be separately receipted in Issue26/PR27. Retention is 30 days; durable archival beyond GitHub retention is not claimed.

## Residual risks and architecture decision

| Priority | Residual risk | Required status / decision |
|---|---|---|
| P0 | Original C-only rollback revives A; real legacy assertion remains unsafe | FAIL_SECURITY / unresolved; do not relabel as fixed |
| P0 | Synthetic W storage/root/channel may roll back or be cloned with the host | Lane2 BLOCKED; assumed invariant is not experimental evidence |
| P0 | Noncloneable actor/guard installation and authenticated verifier root depend on independent infrastructure and trusted operations | Unproved; no technology/custody approval |
| P0 | Unknown OPEN can never be safely cleared by this implementation | Lane3 BLOCKED; no successor authorization, no timeout/manual release |
| P1 | Controller/coordinator/superuser are trusted; obsolete verifier safety requires external quarantine/admission | Excluded adversary/capability boundary; no universal physical-clone proof |
| P1 | INERROR, cancellation, crashes and lost replies may permanently block availability | Deliberate fail-closed; any recovery mechanism needs separate authorization/proof |
| P1 | Tested schedules do not establish all interleavings, linearizability under arbitrary failures, production partition/HA or power-loss safety | NOT_RUN / no formal proof |
| P1 | Catalog manifest is a bounded SQL policy measurement, not complete host/software attestation | Further independent design/experiments required |
| P2 | Synthetic token format/TTLs/HMAC approach and test coordinator interface remain experimental | PROTOCOL_PROPOSED; no APR change or approved contract |

Proposed ADR/CR refinements are in `docs/changes/CR-S0-09F_W_ORACLE_EVIDENCE.md`. Independent read-only review findings and their resolution are in `docs/security/S0_09F_READ_ONLY_REVIEW.md`. The bounded Lane1 observations are ready for Astra Management evidence review; the recommendation supports only **S0-09F_BOUNDED_ORACLE_INTEGRATION_EVIDENCE_ONLY / W_ROOT_AND_ORPHAN_RECOVERY_UNPROVED / PROTOCOL_PROPOSED**. Any scope expansion requires a separate explicit Astra Management decision. No merge or production authorization is requested or implied.

## Source inventory (40 distinct F methods)

Execution status follows the actual matrix/CI receipts above; enumeration alone is not a PASS.

### test_oracle.py

- `OracleContractTests.test_initial_activation_and_stale_cas_denial`
- `OracleContractTests.test_open_is_committed_before_ticket_and_same_key_is_idempotent`
- `OracleContractTests.test_same_key_changed_intent_is_denied`
- `OracleContractTests.test_same_key_retry_cannot_rebind_original_holder`
- `OracleContractTests.test_known_local_read_commit_ack_closes_exact_bound_hold`
- `OracleContractTests.test_checker_cannot_admit_or_close`
- `OracleContractTests.test_orphan_open_blocks_takeover_after_disconnect`
- `OracleContractTests.test_revoke_blocks_new_admission_and_delayed_first_use`
- `OracleContractTests.test_copy_actor_with_wrong_incarnation_or_sid_denies`
- `OracleContractTests.test_declared_continuity_loss_denies_without_reinitialization`
- `OracleContractTests.test_real_oracle_restart_preserves_durable_open`
- `OracleContractTests.test_close_never_overwrites_concurrent_unknown`
- `OracleContractTests.test_attestation_requires_live_hold_and_exact_intent`
- `OracleContractTests.test_old_hold_cannot_attest_under_changed_namespace_or_policy`
- `OracleContractTests.test_revocation_invalidates_previous_attestation`

### test_integration.py

- `IntegrationTests.test_direct_issuer_and_rls_use_online_w`
- `IntegrationTests.test_missing_ticket_and_private_c_fallback_are_denied`
- `IntegrationTests.test_current_w_blocks_old_owner_after_real_c_rollback`
- `IntegrationTests.test_downgraded_verifier_stays_quarantined`
- `IntegrationTests.test_overlay_rollback_reapply_preserves_manifest_acl_rls`
- `IntegrationTests.test_open_survives_last_guard_until_known_commit_and_close`
- `IntegrationTests.test_known_same_transaction_abort_can_close`
- `IntegrationTests.test_replaced_transaction_exception_never_closes_original_as_abort`
- `PoolIntegrationTests.test_pool_commit_and_takeover_reuse`
- `PoolIntegrationTests.test_pool_rollback_and_takeover_reuse`
- `PoolIntegrationTests.test_pool_actual_cancel_and_takeover_reuse`

### test_faults.py

- `FaultTests.test_crash_cuts_durable_open_remain_blocked_across_w_restart`
- `FaultTests.test_crash_before_open_commit_issued_no_permit`
- `FaultTests.test_crash_after_close_ack_allows_new_epoch`
- `FaultTests.test_actual_lost_local_commit_reply_keeps_unknown`
- `FaultTests.test_actual_lost_open_commit_reply_never_issues_permit`
- `FaultTests.test_delayed_open_ack_cannot_start_after_revoke_intent`
- `FaultTests.test_w_outage_denies_existing_rls_issuer_and_new_gate`
- `FaultTests.test_one_channel_partition_denies_without_c_fallback`
- `FaultTests.test_wrong_root_namespace_policy_and_old_actor_are_denied`
- `FaultTests.test_valid_old_signed_response_cannot_satisfy_fresh_challenge`
- `FaultTests.test_paired_takeover_cas_race_has_one_winner_no_early_ready`
- `FaultTests.test_concurrent_local_transactions_hold_independent_bound_operations`
- `FaultTests.test_prepared_transaction_is_actually_prohibited`
- `FaultTests.test_quarantine_drains_existing_pool_and_blocks_direct_login`

