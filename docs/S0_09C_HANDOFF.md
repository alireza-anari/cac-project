# S0-09C — Final evidence and security handoff

Date: 2026-11-05. Audience: Astra Management. Status: **NEW_IMPLEMENTATION_EXPERIMENTAL / PROTOCOL_PROPOSED**.

This is a bounded synthetic recovery-fencing experiment, not production approval, protocol ratification or Sprint 0 completion. [Issue #19](https://github.com/alireza-anari/cac-project/issues/19) remains subject to architecture review. [PR #20](https://github.com/alireza-anari/cac-project/pull/20) remains Draft and unmerged, stacked on `work/s0-09b-issuer-pool-recovery-poc` at `75be54d0f18d6391014ca4e5d91466d62a6cf72c`. SOURCE-001 / GATE-SOURCE remain **BLOCKED**; Architecture Gate #9 remains **OPEN**.

## Revision and evidence provenance

Implementation reviewed: `3a1138885a5c73e0b427a25b858fa399ff56cd24`. This handoff changes documentation only. The delivery receipt in PR #20 identifies the documentation commit and checks attached to that new SHA; the earlier runs below must not be represented as runs of a later documentation SHA.

Source, all five actual GitHub job logs, workflow metadata and artifact metadata were inspected. The independent reviewer separately read the source and logs; neither reviewer reran database tests during this documentation mission. GitHub reports all five runs completed successfully, attempt 1, associated head equal to the implementation SHA. PR workflows actually checked out synthetic merge `0ad97582f90ab23a2ecc1b9b02519c32c707c970`; push workflows provide exact-head evidence.

| Workflow | Run and result | Executed evidence |
|---|---|---|
| S0-09C push | [42046511769](https://github.com/alireza-anari/cac-project/actions/runs/42046511769) PASS | Expected parent RED; 20 distinct cases twice; structural roundtrip; credential scan |
| S0-09C PR | [42046521552](https://github.com/alireza-anari/cac-project/actions/runs/42046521552) PASS | Same matrix on merge ref |
| Full backend push | [42046511716](https://github.com/alireza-anari/cac-project/actions/runs/42046511716) PASS | 43 inherited + 24 S0-09A + 27 S0-09B, each before/after its roundtrip |
| Full backend PR | [42046521752](https://github.com/alireza-anari/cac-project/actions/runs/42046521752) PASS | Same retained floor on merge ref |
| S0-09B focused PR | [42046521525](https://github.com/alireza-anari/cac-project/actions/runs/42046521525) PASS | Additional 27 retained B cases on merge ref |

There are **114 distinct cases across separate workflows**, not 228 distinct cases or a single combined 114-case execution under C wrappers. The 43-case foundation includes 39 PostgreSQL cases and four settings cases. Repetitions and crash subcases do not increase the distinct count. The retained 94 cases were preserved without test changes by this handoff.

The [evidence manifest](evidence/S0_09C_CI.json) records exact run/job/artifact IDs, service-reported archive digests and locally computed job-log SHA-256 values. Artifact digests are GitHub metadata, not independently recomputed archive checksums. Artifacts were available at review and expire around 2026-12-05; the linked Actions logs/artifacts remain the primary raw evidence. Retain them before expiration if long-term audit retention is required.

## Three-cluster experiment and authority

All three servers ran PostgreSQL **17.11**, official image `postgres@sha256:839fbb5a4942a7758dd93e18b42ea5649807491a0545b5eeeb8f0b8bb11857a5`. C logged `fsync=on`, `synchronous_commit=on`, `full_page_writes=on`. These settings plus restart tests establish the observed durability boundary, not power-loss/storage correctness.

| Cluster | Function / port | Push system identifier | PR system identifier |
|---|---|---|---|
| A | Old primary / 5432 | 7704696118501625894 | 7704696137407049766 |
| B | Independently initialized restore / 5433 | 7704696120097562661 | 7704696140973727781 |
| C | External generation anchor / 5434 | 7704696122023723045 | 7704696144357158950 |

A/B use database `cac_s007_test`; C uses `cac_s009c_anchor`. Distinct initialized clusters and storage establish separation from the application logical restore. They share one CI host and network; they are not independent physical failure domains. Retained B workflows use actual **PgBouncer 1.22.0**, package `1.22.0-1build4`. C gates use fresh direct psycopg connections: no combined C-plus-PgBouncer reuse proof exists.

C stores the durable epoch, owner, random generation, request UUID, activation phase and OPEN operation intents. Reservation locks the singleton and performs expected-epoch CAS; a reservation immediately removes old active authority. The local apply starts unready. Confirmation requires a signed ACK obtained through a separate authenticated dblink connection that sees committed local state. An online authority/nonce check is needed for readiness and guarded use. Private unfenced functions lose runtime/issuer grants; wrappers check before and after guarded work.

An OPEN intent is committed on C before local authorization. It binds the operation to local transaction/backend/cluster identity and the anchor holder session. DONE follows a known local transaction outcome and successful anchor completion. **Any OPEN intent blocks takeover. An orphan OPEN also blocks readiness and new guarded use; healthy live gates permit concurrent same-owner operations.** Crash ambiguity can therefore cause indefinite safe downtime. No automatic timeout, safe orphan reconciliation or operator recovery protocol is implemented; test fixture resets are not recovery procedures.

Restore tests actually dump application schemas (`poc`, `poc_private`, and fenced schemas when applicable), then restore to independently initialized B with separate credentials/extensions. C is excluded. Copied readiness and ledger rows do not grant B authority. A live old A is denied after B activation. This is sequential positive/negative probing around takeover, not simultaneous multi-issuer load or a consensus proof. Physical PGDATA/PITR restores preserve system identity and were not tested.

## Attack and negative-assertion matrix

All 20 rows below executed successfully in both C runs, before and after roundtrip. Names map directly to `experimental/backend/recovery_fencing/tests/test_fencing.py` in listed source order. Negative tests include positive recovery where noted; passing negatives are GREEN, not separate mutation RED controls.

| # | Attack / fault | Observed assertion and boundary |
|---|---|---|
| 1 | Unactivated clusters | Three distinct cluster IDs; not ready before activation; A positive afterward |
| 2 | Copy ready state and ledger to B | Copied ledger count 1; B not ready; direct issuance denied without new authority |
| 3 | Keep old primary alive after takeover | B epoch 2 usable; A readiness and issuance denied |
| 4 | Two concurrent expected-epoch reservations | Two threads, one winner; reserved phase leaves both unready; winner activates. No deterministic collision barrier or stress schedule |
| 5 | Duplicate / superseded request UUID | Current retry idempotent; old request cannot resurrect after B takeover. No real lost-response transport injection |
| 6 | Trust-authenticated self-link | Unsafe self-link rejected with SQLSTATE 2F003; authenticated bridge succeeds |
| 7 | ACK of uncommitted apply | Separate reader cannot confirm; rollback leaves reserved/unready; retry succeeds |
| 8 | Direct SQL, role escalation, ticket replay | Private configuration, unfenced API, SET ROLE and no-ticket paths deny; another connection and completed-ticket replay deny |
| 9 | Takeover during long transaction | Takeover times out while gate held; after closing it B takes over and a new A connection denies. Same pooled connection reuse untested |
| 10 | Savepoint / rollback manipulation | Independent first-store ledger survives savepoint rollback; alternate-store issue denied; completed gates leave no OPEN |
| 11 | Anchor unavailable | Actual C stop denies readiness, raw challenge, broker use and reservation; start preserves epoch and restores positive use |
| 12 | Wrong anchor identity | Configured pinned SID changed to 0; readiness/use deny. Actual wrong endpoint or replica routing untested |
| 13 | Replay stale signed attestation | Attest fault returns old nonce proof; readiness/use deny; original function restored and positive path returns |
| 14 | Missing bootstrap / unsafe ACL | Missing B config denies activation; effective issuer EXECUTE on unfenced function explicitly verified true, then activation/readiness deny; REVOKE verified false and retry succeeds. Same grant after activation denies readiness/use; cleanup restores readiness |
| 15 | Wrong committed-reader credential | ACK/confirmation denied; C remains reserved and both nodes unready |
| 16 | Activation worker crash | Five actual process-exit hooks; exact states below; same-request retry stays epoch 1 |
| 17 | Issuer worker crash | Before/after local commit produce ledger 0/1 respectively; durable OPEN remains; takeover and readiness deny |
| 18 | Anchor crash after attested local body | Pause A, SIGKILL/start C, reject B activation; resumed A exits denied; epoch 1, both unready |
| 19 | Restart old A and roll back local state | After B takeover, resetting A generation/epoch/ready does not revive A; B stays usable |
| 20 | Quiescent anchor crash / stale CAS | SIGKILL/start preserves epoch 1; stale expected 0 denies; A positive afterward |

The bootstrap/ACL correction at this implementation SHA preserves denial assertions. A bare REVOKE on `pg_control_system()` did not reliably remove effective access through PUBLIC/membership. The replacement injects and verifies an effective unsafe EXECUTE grant. It demonstrates detection of that grant inventory violation, not that schema USAGE also permits a direct exploitable call. Readiness is a targeted predicate, not comprehensive installation integrity attestation.

### Actual RED/GREEN sensitivity

`parent_red.py` restores the unfenced parent into B and expects old-response issuance to be denied. Both C logs contain the actual assertion failure `InsufficientPrivilege not raised`; the wrapper requires exactly one failure and zero errors before accepting expected RED. Candidate tests subsequently pass. This is meaningful parent-versus-candidate sensitivity for the restore scenario.

**Candidate CAS-disabled, SQL-fence-disabled, duplicate-owner and OPEN-intent-disabled mutation controls were not executed at this SHA.** `run.py` contains a placeholder comment, no tracked candidate sensitivity module or invocation. Earlier design/plan statements describe intended work, not delivered evidence. Retained foundation/A/B sensitivity controls remain evidence for their respective layers and cannot substitute for C mutation sensitivity.

## Crash, rollback and concurrency boundaries

| Injected activation crash | State immediately afterward | Retry |
|---|---|---|
| Before reserve | Empty, epoch 0, unready | Epoch 1 activates |
| After reserve | Reserved, epoch 1, unready | Same epoch activates |
| After committed apply | Reserved, epoch 1, unready | Same epoch activates |
| After confirm | Active at C, epoch 1, local unready | Same epoch activates |
| After ready | Active, epoch 1, ready | Remains epoch 1; completed activation is valid |

These are five subcases of one test; issuance crash has two subcases of one test. `os._exit`, Docker stop/start and SIGKILL/start are real process/container actions. They do not enumerate all instruction boundaries, disk power loss, network partitions or lost COMMIT acknowledgements. An already authorized delayed response/read cannot be retroactively erased.

App A down/up is actually executed between two complete 20-case suites. The comparison includes function definitions/owners/function ACLs, selected columns, constraints and selected `poc` policy fields across the four app schemas. It does not establish whole-database equivalence: schema/table ACLs, all ownership, standalone indexes, sequences, defaults, RLS enable/force flags and data are not comprehensively compared. C anchor migration rollback/reapply is not covered by that snapshot. Uncommitted-apply rollback and savepoint scenarios are separately exercised. Local state rollback after restart is not physical PITR.

Still untested: deterministic/high-load issuance-versus-takeover interleavings; same C-fenced pooled backend reuse; crash at every protocol boundary; real packet loss/asymmetric partition; standby/read-only anchor; missing extension/role fault matrix; actual endpoint substitution; physical backup/PITR/promotion; anchor restore/rollback; multi-host failure and quorum/HA; orphan reconciliation; production latency/RPO/RTO. A two-thread CAS winner test and blocked long transaction do not prove these schedules.

## Trust model and residual risks

Trusted: broker/issuer processes, guard SQL, administrator, OS/kernel, authenticated endpoint identity and non-rolled-back anchor storage. Broker credentials and shared MAC material are inside this experimental trusted boundary. A malicious privileged actor or compromised trusted broker is outside the claimed proof. There is no independent KMS or approved production credential lifecycle. HMAC over PostgreSQL JSONB text and comparison/canonicalization are experimental; v2 format, TTL and key management are not approved contracts.

| Priority | Residual risk / required follow-up |
|---|---|
| P0 | Anchor rollback, cloned identity or malicious administration can violate the assumed monotonic authority. Establish externally governed anti-rollback identity/storage and recovery authority before any broader claim |
| P0 | Safe orphan reconciliation is absent. Do not clear OPEN or enable another owner on timeout; require a separately reviewed external fencing/recovery protocol |
| P0 | Candidate mutation sensitivity and combined pool/fence schedules remain missing proof obligations; retain the architecture gate |
| P1 | One CI host, process-restart durability and logical restore do not establish physical/PITR/partition/HA behavior |
| P1 | Targeted readiness/ACL predicates do not audit the entire installation; trusted admin changes can invalidate assumptions |
| P1 | Production cryptography, TLS, secrets, credential rotation, IdP/MFA, onboarding, performance and operational response are unapproved or outside scope |

These priorities are management risk labels, distinct from the independent review's medium/low evidence findings. No production identity, customer data, public API, onboarding integration or production secret was used by this handoff.

## Independent review and proposed decision

See [read-only security review](security/S0_09C_READ_ONLY_REVIEW.md) for scope, five findings and precise source locations. No additional exploitable bypass was identified within the stated assumptions; this is not a security certification. No executable change was required for this documentation mission.

Proposed vote: **record the observed synthetic evidence with explicit limits; require further proof before architectural acceptance**. Keep `NEW_IMPLEMENTATION_EXPERIMENTAL / PROTOCOL_PROPOSED`, PR #20 Draft/unmerged, SOURCE-001 / GATE-SOURCE BLOCKED and Gate #9 OPEN. Do not merge prior PRs or declare Sprint 0 complete. [Proposed CR / ADR changes](changes/CR-S0-09C-001-recovery-fencing-evidence.md) separate observed invariants from missing experiments and leave decisions to Astra Management.
