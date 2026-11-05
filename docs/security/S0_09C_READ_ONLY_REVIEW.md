# S0-09C independent read-only security review

Date: 2026-11-05. Reviewed implementation: `3a1138885a5c73e0b427a25b858fa399ff56cd24`.

A separate review agent independently inspected all recovery_fencing source, SQL, 20 tests, design/plan, workflow and the five actual CI logs listed in [the handoff](../S0_09C_HANDOFF.md). No source was edited and no database tests were independently rerun. This is a separate analysis of the same evidence, not an external third-party certification or a new execution result.

No additional exploitable fencing bypass was identified within the trusted broker, guard, administrator and non-rolled-back anchor model. Findings concern the limits of that conclusion and of reported coverage.

| Severity | Finding | Source at reviewed SHA / disposition |
|---|---|---|
| Medium | Candidate mutation sensitivity absent | `recovery_fencing/run.py:26` is a placeholder. Design lines 79–81 and plan lines 18–19 describe controls absent from the tracked runner/workflow. Actual RED is `parent_red.py:7–21`. Record gap; do not count parent/A/B sensitivity as C CAS/fence sensitivity |
| Medium | Reused pooled backend fencing unproven | `broker.py:18–19,100` opens/closes fresh connections. `tests/test_fencing.py:102–111` closes the held connection before a new gate denies. Separate B pooling evidence does not combine C wrappers with PgBouncer |
| Medium | Fault matrix narrower than design | Test lines 134–138 change a pinned SID, not the endpoint. Lines 149–198 cover missing config and effective unfenced EXECUTE grant. Removed roles/extensions, standby/read-only authority and network/transport faults are not tested |
| Low | Structural roundtrip comparison bounded | `run.py:14–19` compares function definitions/ACLs/owners, selected columns, constraints and selected poc policies; excludes comprehensive schema/table privileges, defaults, standalone indexes, sequence properties, RLS flags and data |
| Low | Bootstrap readiness is targeted | `sql/up.sql:22–26` checks extension names, effective unfenced EXECUTE denial and wrapper owner/SECURITY DEFINER properties; does not attest all role membership, search path, function definitions or permissions |

Paths above are relative to `experimental/backend/`; design/plan are `docs/superpowers/specs/2026-11-03-s0-09c-design.md` and `docs/superpowers/plans/2026-11-03-s0-09c.md`. Line numbers identify reviewed source, not the documentation commit.

The corrected bootstrap ACL fault verifies effective permission true before denial and false after cleanup. This preserves the security assertions and avoids treating an ineffective REVOKE as a real fault. Separate authenticated committed-reader ACK evidence rejects uncommitted apply and unsafe trust-authenticated self-link; it does not establish distributed atomic commit or arbitrary transport security.

The most consequential availability boundary is the durable OPEN intent. `anchor.sql:24` blocks reservation while any OPEN exists; `broker.py:71` commits intent before local authorization and lines 88–100 close it only after confirmed outcome and anchor finish. Crashed or ambiguous operations can cause indefinite downtime. Fixture reset must never be described as operational orphan reconciliation.

C push is exact-head evidence; C/full/B PR jobs execute synthetic merge `0ad97582f90ab23a2ecc1b9b02519c32c707c970`. The retained 94 and candidate 20 are separate suites. The handoff's attack/crash tables accurately distinguish observed process exits, container failures, logical restore, rollback and two-thread CAS from untested physical PITR, anchor rollback, partitions and general interleavings.

Recommendation, **PROPOSED ONLY**: documentation handoff is sufficient for this mission. Preserve the experimental/proposed status and Draft/unmerged PR. Record availability costs and proof gaps; require further evidence before architecture acceptance. This review neither approves the protocol nor requests an executable change.
