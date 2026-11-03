# S0-09B architecture handoff — evidence in progress

**NEW_IMPLEMENTATION_EXPERIMENTAL / PROTOCOL_PROPOSED**. Issue #17,
[stacked Draft PR #18](https://github.com/alireza-anari/cac-project/pull/18),
base `work/s0-09a-trusted-context-poc` at
`f351e26aa93ec87f17366dbaff85a87b171d36d2`. Do not merge.

Source identity: CAC-NEW-ORIGIN-S0-07. No historical source recovered.
SOURCE-001 / GATE-SOURCE BLOCKED; architecture #9 OPEN.
PR #11 and PR #16 were reverified Draft/open/unmerged before branching.
No production identity, MFA provider, public API, onboarding, business mutation,
customer data, deployment or production secret is involved.

## Delivered scope

Local issuer process with kernel-checked peer identity, role-only credential
file/environment and independent DB COMMIT-before-return. Actual runtime UID
uses real PgBouncer transaction pooling. Actual database restart and logical
schema/data restore are exercised separately from controlled clock fault
injections, real elapsed expiry and contention/cancellation/deadlock schedules.

See [reproduction and test matrix](../experimental/backend/pool_recovery/README.md),
[residual P0/P1 risks](../experimental/backend/pool_recovery/RISKS.md), and
[proposed CR/ADR decisions](changes/CR-S0-09B-001-recovery-pool-contract.md).

## Initial evidence (not final acceptance)

[Initial push 41581543249](https://github.com/alireza-anari/cac-project/actions/runs/41581543249)
on `f22dd2556fa24cd087bd790b0d8faf98cff74d46` failed at child process startup.
It preserved and passed all inherited 43 tests and all 24 S0-09A cases,
each before/after their rollback/reapply. The new fixed-clock challenge,
expiry, MFA, cleanup and encoding tests passed on PostgreSQL; process/pool/
recovery tests did not execute successfully. This failed run is not evidence of
process isolation or pool safety. No SQL checks were relaxed in response.

Actual package install passed: PostgreSQL **17.11 (Debian 17.11-1.pgdg12+2)**,
PgBouncer **1.22.0**, exact Ubuntu package **1.22.0-1build4**.
Inherited locked Python/Django/psycopg versions unchanged.

Local environment had no PostgreSQL/Docker and denied Unix socket creation;
local AST/request-validator checks only are not database evidence. CI is the
execution authority. Startup diagnostics redact all known fixture credentials.

## Migration and contract diff

Inherited Django migrations, models, SQL functions, policies, grants and all
67 tests remain unchanged in git. Added runner temporarily mutates only the
explicitly disposable database and restores exact function definitions, then
requires structural down/up equality. No persistent schema or public API diff.
v2 bytes and 5s/60s/120s/300s numbers are test inputs, not ratified contracts.

Final-head receipts, results, independent review and concrete findings will
replace this in-progress status after actual verification.
