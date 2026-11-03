# S0-09B residual risks and unsupported scenarios

Status: NEW_IMPLEMENTATION_EXPERIMENTAL / PROTOCOL_PROPOSED. These remain open
even if every test passes. Severity is experiment/integration gating priority,
not a production certification or CVSS score.

| Priority | Residual risk / limitation | Required follow-up |
|---|---|---|
| P0 | PostgreSQL admin/guard/issuer and host root remain trusted; keys live in DB | approve custody/rotation/blast radius and hardened deployment boundary |
| P0 | Valid stolen bearer proof can request its own authorized scope | design actual identity/session/proof delivery and theft response; no real IdP integration here |
| P0 | Restoring keys+generation+ledger does not automatically fence old authority | durable externally coordinated generation fencing before traffic; reject unfenced/split-brain recovery |
| P0 | No PITR, promotion, replication consistency or crash-at-COMMIT proof | separate HA/recovery acceptance plan; verify RPO/RTO and uniqueness after timeline changes |
| P0 | v2 jsonb::text encoding is server-specific; SQL MAC string comparison not proven constant-time | independent protocol/security review, typed canonical vectors and MAC implementation decision |
| P1 | Revocation waits behind active verifier SHARE locks; long transactions extend wait | define bounded in-flight authority, lock/statement timeouts and cancellation policy |
| P1 | Only READ COMMITTED, bounded localhost schedules and small concurrency tested | higher isolation, distributed load/failure schedules and performance/revocation budgets |
| P1 | PgBouncer 1.22.0 exact package is a fixed experimental target, not a recommended deployment version | approved supported version/patch/security review and compatibility matrix |
| P1 | Pooler holds runtime credential; no pool-user override or multi-host/TLS deployment test | harden deployment credentials, transport and administrative access separately |
| P1 | `pg_cancel_backend` tested; protocol CancelRequest, packet loss, split responses, exhaustion not exhaustively tested | cancellation forwarding, lost response/idempotency and service admission design |
| P1 | No bounded thread/admission deployment protocol, anti-DoS, authenticated proof transport or general OS sandbox certification | separate service operational hardening; local UID proof alone is insufficient |
| P1 | Logical restore is schema/data clone on same cluster with roles retained | fresh-cluster role/ACL/bootstrap/extension restore and backup access policy |
| P1 | Exact edges use frozen DB-function clocks; elapsed test cannot prove microsecond scheduling | ratify temporal semantics, skew authority and clock failure handling |
| P1 | No domain writes, public API, onboarding, production audit/outbox | require separately authorized business/identity contracts and acceptance tests |

SOURCE-001 / GATE-SOURCE remains BLOCKED; architecture gate #9 remains OPEN.
No Sprint 0 completion, baseline acceptance, production authorization or merge.
