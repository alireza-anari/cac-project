# S0-09B — synthetic process / pool / recovery experiment

**NEW_IMPLEMENTATION_EXPERIMENTAL / PROTOCOL_PROPOSED.** Implements Issue #17,
stacked on PR #16 at f351e26aa93ec87f17366dbaff85a87b171d36d2. No approved
product protocol, canonical baseline, recovered historical source or merge.
SOURCE-001/GATE-SOURCE BLOCKED; architecture #9 OPEN; APR-033/034/035/036 unchanged.

## Execution boundary

The root CI **test orchestrator** alone has all-role fixture access. It creates
three unprivileged Linux processes, with no supplementary groups:

| Process | UID | Credentials | Interface |
|---|---:|---|---|
| Issuer | 62001 | only `cac_ctx_issuer` login, direct DB | Unix socket, kernel SO_PEERCRED admits UID 62002 |
| Runtime | 62002 | only `cac_ctx_runtime`, synthetic proof | real PgBouncer TCP on CI localhost |
| PgBouncer | 62003 | runtime DB password | transaction pools `one` (1 backend), `many` (4) |

Mode-0600 private files belong to their individual UIDs; socket parent is
root-owned 0755 and cannot be replaced by runtime. Child environments contain
only PATH, LANG and PYTHONDONTWRITEBYTECODE. Neither service imports the all-role
harness. Tests query SQL under the actual runtime login and attempt role
escalation; they also try reading issuer config and `/proc/issuer/environ`.
The fixture administrator is not the runtime adversary. Root/ptrace-capable
host compromise is outside this proof.

Issuer validates exact request fields, sizes, UUIDs, action and JSON body;
rejects duplicate keys/nonfinite JSON; authenticates the peer UID; performs
parameterized fixed SQL; commits and closes its independent DB transaction
before returning a token. SQL remains the final proof/Store/target authorizer.
A stolen *invalid or differently scoped* proof is rejected. A stolen valid
bearer proof for its own authority is NOT solved by UID isolation. No real
identity, proof distribution or MFA provider is implemented.

Synthetic HMAC keys remain in the PostgreSQL guard boundary; this proves neither
external key custody nor isolation from DB admin/guard/compromised issuer.

## Reproduction

Use `.github/workflows/experimental-backend.yml` on Ubuntu 24.04. Official
PostgreSQL 17.11 image is pinned by digest in that workflow. PgBouncer is pinned
to Ubuntu `1.22.0-1build4` (binary 1.22.0), and package/version evidence is captured.
This deliberately fixed test version is not a deployment recommendation.
Python 3.12.15 and all inherited wheels remain hash-locked. The lab requires
Linux UID switching, Docker access to the disposable service and root **test
orchestration only**. Refuses a missing disposable flag or wrong database name.

After existing bootstrap and PoC migration:

```bash
sudo --preserve-env=CAC_TEST_CONFIG,CAC_EVIDENCE_DIR,CAC_EXPERIMENTAL_DISPOSABLE,CAC_POSTGRES_CONTAINER,PYTHONPATH,PYTHONDONTWRITEBYTECODE,PATH "$(which python)" -m pool_recovery.run
```

The workflow runs all inherited 43 cases (39 PostgreSQL + 4 settings subprocess)
and all 24 S0-09A PostgreSQL cases unchanged before/after their rollback paths.
S0-09B runner checks its exact test inventory, forbids skips, runs its suite,
requires assertion RED for deliberately removed transaction binding/MFA/window
checks, restores exact definitions in `finally`, performs PoC SQL down/up with
structural equality, and runs its suite again. Inherited test and SQL files
are not edited by this change. There is no persistent schema migration delta.

## Test matrix

| Group | Real evidence / negative control |
|---|---|
| Process | UID/file/proc denial; runtime SQL/SET ROLE rejection; peer authentication; malformed/oversize/duplicate RPC; deferred COMMIT failure; stopped issuer; truncated EOF |
| Pool | login/current_role/PID/xid witnesses; pinned transaction PID; same PID with different xid across clients; deliberately leaked session SET; rollback/savepoint; cancellation 57014, aborted transaction 25P02, division error 22012 |
| Concurrency | four simultaneous backends, separate S1/S2 reads; acknowledged revoke plus 12 failed retries; issuance blocked behind principal revocation; lock_timeout; Store epoch lock witness; actual injected deadlock and safe next transaction |
| Timing | exact 5s inclusive issue edge, exp exclusive edge, 300s inclusive MFA edge, 120s exclusive purge edge, negative/future clocks, future iat skew; separate real 60+ second expiry and MFA stale-after-issue waits |
| Recovery | actual Docker PostgreSQL restart: ledger equality, dead old transaction and rejected old token; actual pg_dump/pg_restore to another disposable database; explicit generation change; stale proof/session denial |
| Encoding | typed Unicode/numeric/array/duplicate examples; Python HMAC verification of exact PostgreSQL bytes; noncanonical but correctly MACed bytes rejected |

Exact-equality tests temporarily replace `clock_timestamp()` in the target
function with a fixed timestamp, using trusted administrator fault injection,
then restore the exact original definition. They exercise the actual predicates
and database rows without claiming wall-clock scheduling at a microsecond.
Elapsed tests do not replace the clock. Neither class establishes product
latency or revocation SLAs. Numeric precision is preserved with Decimal fixtures.

## Recovery and operational limitations

The logical restore test deliberately demonstrates a dangerous unfenced state:
restoring keys, generation and ledger to another database preserves the issuer's
ability to return the same ledger response to a still-current original
challenge. Explicit new generation fencing rejects it. This is a proposed
operational precondition, not an automatic recovery mechanism added to SQL.
Tokens remain PID/xid bound; no cross-database successful RLS replay is claimed.
The clone is on the same PostgreSQL cluster, with existing roles, a logical
schema/data restore and a fresh pgcrypto extension. This is not physical PITR,
replica promotion, split-brain prevention, crash during WAL flush, backup
confidentiality certification or HA failover evidence. Restart is controlled
Docker restart, not power loss. Dumps contain synthetic keys and never become
uploaded artifacts.

PgBouncer uses actual per-login pools, SCRAM, transaction mode and the default
`server_reset_query_always=0`; no forced server user or reset workaround hides
session-state leakage. Safety depends on checking both xid and PID every time.
Only transaction pooling is tested; session/statement pooling, protocol-level
CancelRequest forwarding (cancellation here is `pg_cancel_backend`), driver
prepared statements, network partitions and rolling pool upgrades are unproven.

Verifier shared locks serialize revocation with an already-authorized active
transaction. Revocation can wait for that transaction to finish. It cannot
retroactively undo already returned reads. The deadlock test deliberately uses
opposite administrator lock order; it proves failure/rollback cleanup in the
observed schedule, not general deadlock freedom. Isolation level is default
READ COMMITTED; higher isolation and every retry schedule remain unsupported.

No public socket, HTTP API, production identity/MFA, customer data, business
writes, onboarding, live deployment or production secret is introduced.
