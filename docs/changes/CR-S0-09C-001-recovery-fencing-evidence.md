# CR-S0-09C-001 — Proposed recovery-fencing evidence and decision boundaries

Status: **PROPOSED**, 2026-11-05. No contract or production approval is created.

References: [Issue #19](https://github.com/alireza-anari/cac-project/issues/19), [Draft PR #20](https://github.com/alireza-anari/cac-project/pull/20), [handoff](../S0_09C_HANDOFF.md), [independent review](../security/S0_09C_READ_ONLY_REVIEW.md). Implementation evidence is pinned to `3a1138885a5c73e0b427a25b858fa399ff56cd24`.

## Proposed ADR amendments for management review

1. Record independent generation authority as a candidate architecture: monotonic epoch CAS, explicit owner/phase, committed-reader ACK and fresh per-operation authority checks. App restore must not restore authority. These are observed synthetic invariants, not approval of the current protocol encoding.
2. Explicitly require no anchor rollback/cloning and trusted broker/admin/endpoint assumptions. Specify how identity and monotonicity survive physical restore before approving that recovery mode; system identifier alone is insufficient for physical clones.
3. Record the conservative durable OPEN rule: ambiguity stops authorization and takeover. Prohibit automatic expiry/cleanup as an availability shortcut. Design safe externally verified fencing and reconciliation separately, including crash/lost-outcome evidence and operator authority.
4. Bound readiness to the predicates actually checked. Treat comprehensive role/extension/wrapper/transport integrity as separate installation requirements and tests.
5. Mark candidate-specific mutation controls, C with reused PgBouncer backend, physical restore and asymmetric partition schedules as outstanding acceptance evidence. Correct earlier design/plan aspirations through this handoff; do not silently interpret them as executed results.

## Proposed follow-up proof gates

| Obligation | Required reviewable evidence |
|---|---|
| Candidate sensitivity | Deliberately disable CAS, SQL fence and OPEN protection independently; each targeted negative assertion must fail for the intended reason, then pass after exact restoration |
| Pool composition | Actual C wrappers through PgBouncer, identify reused backend, hold/cancel/rollback across takeover and assert old context denies on that same backend |
| Recovery identity | Physical restore/PITR and anchor rollback experiments; externally governed fresh authority and old-primary fencing policy |
| Ambiguous operations | Crash/lost COMMIT outcome and orphan reconciliation design with explicit safe recovery; no timeout bypass |
| Fault completeness | Deterministic concurrency schedules, actual wrong endpoint/standby, role/extension faults and one-way network outage, without weakening assertions |

Retain all 94 inherited cases and the 20 C cases. Run separately identified exact-head and merge-ref CI before/after applicable rollback, retain raw artifacts, and report unsupported modes explicitly. Neither v2 context format, TTL values, MAC serialization, secrets nor key management becomes an approved contract.

Proposed disposition: accept the handoff as an evidence record, **defer architecture acceptance pending further proof**. Keep SOURCE-001 / GATE-SOURCE BLOCKED, Gate #9 OPEN and PR #20 Draft/unmerged. No prior PR state changes, production integration, real IdP/onboarding or Sprint 0 completion are authorized by this CR.
