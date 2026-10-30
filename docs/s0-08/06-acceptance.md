# Implementation-ready acceptance plan

**DESIGNED / NOT_RUN / PROPOSED.** No case below is a PASS from S0-08. Architecture must approve [decisions](07-decisions-risks.md) and a new implementation mission before creating this harness. Run against newly migrated disposable PostgreSQL, actual nonowner application logins and synthetic identity/session/key fixtures. Never substitute SQLite.

## Reproducible harness and evidence

Pin approved Python/Django/driver/PostgreSQL/image/optional PgBouncer versions and record digests at execution; S0-07B used Python 3.12.15, Django 5.2.18, psycopg 3.3.6, PostgreSQL 17.11 but that is not a future toolchain approval. Fixture: Tenant A/B, Stores A1/A2/B1, owners OA/OB, manager M, verified target T, unrelated U, inactive D; high/low-risk capabilities and fresh/stale MFA; two or more real DB logins/connections plus restricted lock observer. Identity adapter fixtures simulate the authoritative boundary, not bypass it by setting request.user or a raw GUC. HTTP tests enforce CSRF checks and real session lifecycle with test-only authentication adapter; provider conformance remains separately BLOCKED.

Suggested future runner contract (paths do not yet exist): `PYTHONPATH=. python -m unittest discover -s integration_tests -p 'test_*.py' -v`, from the approved backend root. Suggested groups: test_identity.py, test_context.py, test_pool.py, test_onboarding.py, test_races.py, test_audit_outbox.py. Runner must fail, not skip, when PostgreSQL/required pool/observer is unavailable in a required gate. Set up roles/bootstrap, migrate, `manage.py check`, `makemigrations --check --dry-run`, show migration graph; run entire suite, migration zero/reapply structural comparison, then suite again. Existing S0-07B 43 tests remain a regression floor on its own branch; no new tests are claimed executed here.

Every case records case id/fixture version, source head and synthetic merge SHA, DB schema revision, versions, role flags, isolation, independent PIDs, bounded lock-wait/commit ordering, SQLSTATE, retries, expected/observed postconditions, exit code and redacted log. Capture events/rows from a new correctly scoped connection after commit; use separate observer privilege only for metadata. Never print cookie, challenge signature, key or invitation token. Explicit artifact allowlist; no environment/database dump. CI must associate artifacts with exact tested commit and retention period, and demonstrate relevant weakened-fixture failures restored before the complete green suite.

## Identity / context cases

| ID | Setup / action | Required oracle |
|---|---|---|
| ID-01 | Real login then old/new cookie; logout; expired idle/absolute sessions | Old/expired/revoked handle cannot issue context or mutate; new valid session works; no actor swap |
| ID-02 | Missing/wrong CSRF on login, invite, accept, revoke; hostile Origin/Referer; valid same-origin control | Denied before business effects; no new outbox; approved generic response; legitimate CSRF works |
| ID-03 | Same email from distinct provider subjects; unverified/disabled principal; fake owner field | No account linking or owner creation; immutable target/principal remains correct |
| ID-04 | Rotate session on login/step-up; recover/reset MFA/password; reuse prior MFA proof | Old session/epoch denied; recovery is not fresh MFA; cross-session proof rejected |
| ID-05 | First owner with verified email but absent contact/domain readiness | Onboarding proposal may succeed if eligible; public Live still denied; APR-033/034/035 gates unchanged |
| ID-06 | Worker requests arbitrary principal/scope/MFA/action/target; replay valid session for unauthorized Store | Issuer rejects unsupported derived claims; no token/DB effects; valid own-scope control succeeds |
| ID-07 | MFA at approved threshold and threshold+1, future time, wrong method/session; high-risk vs low-risk action | Exact fresh/expired decision; no nondelegable grant; no owner mutation via manager |
| CTX-01 | Missing/null/duplicate/wrong-type/oversize/unknown-version claims; invalid UUID/tx/PID; wrong role/purpose/action/body | Standard authorization failure, no rows/mutations; positive canonical token works |
| CTX-02 | Alter payload/signature, unrecognized kid/algorithm, wrong audience/environment/generation, fabricated challenge | No downgrade/fallback; arbitrary SQL cannot create usable context |
| CTX-03 | Same token in another transaction/PID/Store/session/body; repeat consumed mutation | Replay denied or exact idempotent history returned without new effects; read context never authorizes write |
| CTX-04 | Stage new key; activate; old verify-only overlap; retire/revoke; cache lags | Valid lifecycle only; revoked/retired key fails; outage never uses prior signer silently |
| CTX-05 | TTL boundary, exp<=iat, far future iat, drift, txid/PID reuse after restore | Proposed limits enforced; generation invalidates pre-restore contexts; long statement bounded |
| CTX-06 | Issuer/identity/key-registry outage or slow response; logs/error injection | Rollback and safe transient denial; no domain SQL without authority; secrets absent from artifacts |

## Database, session revocation and pool cases

| ID | Setup / action | Required oracle |
|---|---|---|
| DB-01 | Runtime/provisioner/onboarding attempt SET ROLE, DDL, TRUNCATE, key access and direct DML | Actual nonowner/NOBYPASSRLS flags; exact denial. Named authorized action positive control works |
| DB-02 | Cross-tenant/store composite references and scoped reads/writes | Correct FK failures and RLS denial; capability not substituted by membership; no data from A2/B1 under A1 |
| DB-03 | PUBLIC and unrelated role call verifier/action functions; future function default ACL; hostile search_path | No implicit execute or object shadowing; approved roles only; function owner not table owner/BYPASSRLS |
| DB-04 | Bypass app validation with direct SQL/named function args differing from signed digest/target | Gate rejects; no audit-success/outbox; RLS remains enabled/forced for every scoped table |
| AUTH-RACE | Actor capability revoke or principal/session deactivate vs ongoing sensitive command, both enforced orders | Shared/exclusive guard blocking witnessed. Command-first may commit before revoker; revoke-first rejects stale authority. No authorization after completed revoke using old epoch; still-authorized Store-snapshot refresh is distinct from revoked actor/session denial |
| POOL-01 | Same backend PID reused for A1 then B1 then unauthenticated request | No A1 context/rows in later request; each transaction has fresh challenge/token |
| POOL-02 | Commit, full rollback, savepoint rollback before context, cancel, exception during install | Context absent; outer transaction aborted if installation undone; no partial business effects |
| POOL-08 | Direct SQL: savepoint before install A, read A, rollback savepoint, request/install different valid scope B in same outer transaction; repeat after ledger retention | Issuer independently committed tuple prevents B; old transaction challenge fails age window after purge; no cross-scope switch. Same authorized tuple cannot extend expiry. Test outage/concurrent issuance for ledger atomicity |
| POOL-03 | Token outside explicit transaction; streaming/lazy ORM after exit | Reject unsupported path; no domain query with retained context |
| POOL-04 | Two threads/tasks with different principals; shared connection misuse | Independent valid connections work; shared/overlapping transaction rejected, no context cross-talk |
| POOL-05 | Direct, session pool and separately approved transaction pool; forced same server-login misconfiguration | Correct login preserved; tx/PID pinned for transaction; forced shared login rejected. Statement pooling rejected |
| POOL-06 | Connection drops before/during/after commit; exhausted locks; deadlock/serialization retry | Unknown commit resolved by current-auth idempotency lookup; retries bounded/re-authorized/new tokens; no duplicate effects |
| POOL-07 | Pool returns dirty session-level GUC/role/search_path, stale prepared plan, reconnect/failover | Discard/alert; no implicit trust in reset; generation/epoch mismatch fails; approved clean control works |

## Provisioning and durable side effects

| ID | Fault / action | Required oracle |
|---|---|---|
| ONB-01 | Same first-store key/body in parallel; changed body; different keys same enrollment; inject failure after each insert | One eligible enrollment; consistent resources/result; conflict for changed payload; full rollback on fault |
| ONB-02 | Wrong target/token/Store, unverified target, missing invitation, expired/accepted/revoked token | Uniform approved safe disclosure; zero new grants/outbox; no identity reactivation |
| ONB-03 | Revoked/inactive inviter or reduced delegable subset after issue; stale MFA high-risk accept | Fail under current authority; issue-time authority alone insufficient; owner/manager limits preserved |
| ONB-04 | Zero grants + pending matching invitation revoke; existing grants + multi-cap pending; unrelated rows | SEC-REV-001 preserved exactly; whole matching multi-cap invite revoked; unrelated grants unchanged |
| ONB-05 | Repeat revoke and accept replay, lost response then retry after later revoke | No duplicate effective audit or timestamp churn; history response never revives grant |
| ONB-06 | Concurrent issue/revoke in both orders; issue after completed revoke | Issue-first canceled, revoke-first new invite allowed; no permanent invitation ban |
| AUD-01 | Fault after grant mutation, invite transition, audit insert, outbox insert | One transaction rolls back all success effects; separate denial event never claims success |
| AUD-02 | Direct app update/delete audit, unauthorized outbox claim/cross-store lease | Denied; unique scoped correlation/sequence; privileged fixture not counted as app success |
| AUD-03 | Worker crash before send, after send before ack, redelivery and dead-letter recovery | At-least-once event, dedupe by id; no DB business rollback/regrant from delivery retries |
| AUD-04 | Scan application/DB/proxy/APM logs, artifacts, idempotency result, expired encrypted envelope | No raw secrets; approved expiry/erasure; no secret replay through retry response |

## Exact mapping of the eight historical PostgreSQL race scenarios

Source: [original plan at main](../../standalone/onboarding/docs/POSTGRES-ACCEPT-REVOKE-RACE-PLAN.fa.md). The source plan remains DESIGNED/NOT_RUN, historically blocked on SOURCE-001/DB-001. This proposal permits a **new-origin** future harness only after #9 contract approval and security environment readiness; it does not relabel that original plan as executed or recovered integration.

All cases use actual service/gateway calls through nonowner roles; two independent connections A=accept, R=revoke, third restricted observer. Fixture T/A1 pending invitation with zero active grants; variants below. READ COMMITTED proposed. For ordered cases: first worker obtains Store guard and signals a one-way event; launch second, prove `pg_blocking_pids(second_pid)` includes first; only then release first to commit. Never put a two-party barrier after a mutually exclusive lock. Use monotonic deadlines (propose 10 seconds for coordinator, shorter DB waits adjusted for deliberate witness); record timeouts as failure/invalid test, not PASS. Independent final scoped query supplies oracle; no cached ORM snapshot.

| Existing ID -> future case | Required schedules / variant | Final oracle and evidence |
|---|---|---|
| PG-RACE-01 -> test_revoke_before_accept | R locks first; A demonstrably waits; R commits | A denied old invitation, no active target capability, pending-only revoke audited once, no accepted-success audit |
| PG-RACE-02 -> test_accept_before_revoke | A locks first; R waits; A commits | A may succeed; R then revokes resulting grant; zero active target capability after both; accepted history retained; both effective audits |
| PG-RACE-03 -> test_existing_grant_and_pending | Active grant + pending, run both orders | Both old authority paths removed, no resurrection; unrelated grants preserved |
| PG-RACE-04 -> test_multicap_scope_isolation | Multiple/multi-cap invites T/A1 plus U/A1, T/A2, T/B1; both orders | Whole matching pending invitation revoked; other target/store invitations unchanged; accepted-first grants follow capability-specific revoke |
| PG-RACE-05 -> test_fault_rollback_retry | Inject after grant change, invite invalidation, audit/outbox write; then bounded retry | No partial durable rows/audit/outbox; eventual authorized retry has one effective outcome |
| PG-RACE-06 -> test_double_revoke_replay | Two revoke workers, both orders; replay request | One effective revocation audit, stable revoked timestamps; no invitation activation |
| PG-RACE-07 -> test_unordered_stress | Start barrier BEFORE lock, >=100 fresh-fixture/key iterations | Outcome equivalent to 01 or 02; after successful completion zero old authority; all retries/SQLSTATEs visible, timeout not hidden |
| PG-RACE-08 -> test_new_invite_after_revoke | Complete revoke; authorized new issue/accept; replay old token | New token can grant; old token denied; no global deny tombstone |

Issue/revoke and actor/session revocation races are ONB-06/AUTH-RACE additions, not falsely counted among the historical eight. A legal serialization abort or authenticated Store-epoch refresh (PZ001 proposed) requires recorded bounded retry and final oracle, not merely “one worker failed.” In accept-first, acceptance increments the Store epoch: a waiting still-authorized revoker may need rollback/new context and a second attempt before revoking the grant. Record the initial blocking witness and every fresh-context attempt. Revoke-first acceptance ultimately fails on the old terminal invitation, never silently revives it. Actor/session revocation is a denial, not an epoch-refresh opportunity. Exhausted retries fail the acceptance run; do not count an incompletely executed revoke as a secure final state. No concurrency PASS if lock witness, fresh final observer or actual nonowner execution is missing.

## Gate criteria

IDENTITY: ID cases + AUTH-RACE pass with reviewed adapter; live provider assurance remains separate. CONTEXT: all CTX cases plus DB privilege checks and key lifecycle proof. POOL: all modes actually selected pass POOL cases; unsupported modes excluded by configuration. ONBOARD/CONCURRENCY: all ONB/AUD and every PG-RACE schedule pass with audit/outbox invariants. MIG: up/down/reapply proof and clean Django checks on new schema. Any security violation is FAIL; missing environment/contract/observer is BLOCKED; unselected mode is explicitly SKIPPED, never a complete gate PASS. Architecture/security review and exact-head push + PR CI are required for future implementation acceptance. Historical SOURCE and product release gates remain independent and blocked.
