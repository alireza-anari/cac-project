# CR-S0-09B-001 — proposed recovery / pool / issuer contract questions

Status: **PROPOSED**, experimental only. Issue #17 / Draft PR #18. Does not
change APR-033/034/035/036, historical freeze, any API or product policy.
Review parent: S0_09A_ARCHITECTURE_RULING.md on main, reviewed head f351e26.

## Requested architecture decisions (not self-approved)

| Area | Existing experiment | Proposed decision for separate review | Delta delivered here |
|---|---|---|---|
| Process | issuer role callable in a Python test process | runtime deployment principal must not read issuer credential or invoke unrestricted signing | isolated UID, minimal file/env, kernel peer checked local RPC, SQL authorizer retained; private randomized fixture admin credential closes public-bootstrap bypass |
| Pool | no actual PgBouncer evidence in S0-09A | transaction context must be installed/used in the pinned transaction; check login+xid+PID on every use; no reliance on reset | one/four backend pools, hostile session SET, cancellation and reuse tests |
| Restore | ledger/key/generation restored together | new generation must be fenced before restored service accepts requests, with single-authority recovery procedure | measured unfenced clone behavior, manual fixture generation change; **no automatic recovery protocol** |
| Time | proposed 5/60/120/300 second values | decide inclusive issue/MFA and exclusive token/purge edges, clock/skew behavior and long-transaction policy | controlled exact SQL clocks and separate elapsed tests; values unchanged |
| Revocation | guard SHARE locks serialize active transactions | define acknowledged revoke, bounded wait/cancel/retry and accepted in-flight-read semantics | observed lock/deadlock/cancel schedules and post-commit retries; no SLA |
| Encoding | HMAC of PostgreSQL jsonb::text hex payload | approve typed canonical bytes, duplicate/numeric rules, cross-implementation vectors and constant-time MAC verification separately | typed comparison and Python MAC calculation only; format unchanged |
| Custody | synthetic HMAC keys in guard-owned DB | decide external custody, rotation, issuer/admin compromise and backup confidentiality | **no production key-management implementation** |

## Schema and API diff

No persisted SQL schema/function/grant delta to S0-09A. No Django model or
migration diff. No public HTTP API/OpenAPI/onboarding change. Local RPC is an
experimental transport only: exact fields `challenge`, `proof`, `store`,
`action`, `target`, `body`; generic denied response or committed token. It is
not a product identity or signing interface. Test administrator temporarily
replaces function clocks/security predicates and restores their exact definitions.

Rejecting restore without externally durable fencing, or moving keys out of
the DB, will require another design/implementation slice. A positive test run
cannot ratify those choices. Management/Architecture must assess evidence and
residual P0/P1 risks before any integration contract work is authorized.
