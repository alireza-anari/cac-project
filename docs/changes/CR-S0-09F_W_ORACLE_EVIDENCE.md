# Proposed CR — S0-09F conditional integration evidence

**W_ORACLE_ASSUMED / LANE1_ONLY / ROOT_AND_ORPHAN_RECOVERY_UNPROVED**

Status: **PROPOSED**, for Astra Management/architecture review only. This file does not amend APR-033/034/035/036 or any approved contract. SOURCE-001/GATE-SOURCE BLOCKED; Architecture Gate9 and Issue23 OPEN. No historical source recovery, Sprint0 completion, merge or production approval.

| Proposed clarification | Experimental reason | Decision boundary |
|---|---|---|
| Separate conditional integration evidence from W-root nonrollbackability | A current W fixture may deny C rollback while the inherited C-only assertion still fails | Retain legacy FAIL_SECURITY. Lane2 remains BLOCKED/NOT_RUN; independent root infrastructure/custody design needs explicit authorization |
| State external admission and obsolete-verifier quarantine as trusted obligations | Restored pre-W code cannot prove its own rejection. NOLOGIN must commit before draining sessions and replacing SQL | Current bounded logical-restore scope only; no physical clone/noncloneable identity claim |
| Bind permits to immutable operation, digest, idempotency key, actor incarnation and exact transaction | A repeated key must not recreate authority or transfer a holder; pool reuse changes fullxid even with same PID | Interface is a test proposal, not approved format/API |
| Distinguish revoke intent from completed takeover | Existing local work may still commit after last guard; durable OPEN prevents a live successor during uncertainty | Do not claim instantaneous cancellation of already validated transactions |
| Require atomic CLOSE-versus-UNKNOWN state transition | Actual concurrent update race overwrote UNKNOWN in early candidate | Lock/check operation row; UNKNOWN is terminal for this lane. No recovery/clearing transition authorized |
| Treat transaction identity/outcome ambiguity as durable exclusion | INERROR cannot confirm original fullxid; replacement COMMIT/BEGIN and lost ACK cannot be guessed as ABORT | Fail-closed availability loss accepted for bounded proof. Future recovery requires separate Management decision and proof |
| Preserve evidence taxonomy | Feature/parser/ACL setup errors differ from intended security assertion RED and legacy unsafe FAIL_SECURITY | Record actual checks/counts/SHA/source identity; workflow success alone is not recovery-security success |

Recommended future decision, only after final bounded evidence review: accept the *conditional test observations* for Lane1 while retaining **S0-09F_BOUNDED_ORACLE_INTEGRATION_EVIDENCE_ONLY / W_ROOT_AND_ORPHAN_RECOVERY_UNPROVED / PROTOCOL_PROPOSED**. Do not authorize any Lane2 root, KMS/quorum/HA, W restore/rebootstrap, Lane3 orphan clearing or production implementation on the strength of this experiment. Any next experiment or scope expansion needs a separate explicit decision.
