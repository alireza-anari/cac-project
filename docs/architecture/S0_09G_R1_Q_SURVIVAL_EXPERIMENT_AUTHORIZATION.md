# CAC — S0-09G R1 Review and Bounded Q-Survival Experiment Authorization

**Date:** 2026-11-06  
**Role:** Astra Management / CAC Architecture  
**Reviewed independent delta PR:** [#30](https://github.com/alireza-anari/cac-project/pull/30), exact head `6608a644b20dc091fe38137e1bd593c676c188c2` (one docs-only report; base `main` at `3dcd1c0896d05be2097ad7aa64f774a66e816043`)  
**Report:** [S0-09G R1 independent delta review](https://github.com/alireza-anari/cac-project/blob/6608a644b20dc091fe38137e1bd593c676c188c2/docs/security/S0_09G_R1_DESIGN_DELTA_REVIEW.md)  
**Management R1:** [Targeted root refinement](S0_09G_TARGETED_ROOT_REFINEMENT_R1.md), unmodified  
**Execution authorization:** [S0-09H Issue #31](https://github.com/alireza-anari/cac-project/issues/31), P0  
**Decision:** `S0_09G_R1_DESIGN_REVIEW_ACCEPTED / S0_09H_Q_SURVIVAL_EXPERIMENT_AUTHORIZED_ONLY / REAL_ROOT_ANTIROLLBACK_UNPROVEN / LANE3_BLOCKED / NO_MERGE`  
**Source classification:** `CAC-NEW-ORIGIN-S0-07 / NEW_IMPLEMENTATION_EXPERIMENTAL / PROTOCOL_PROPOSED`.

## Adjudication

**Accept** the independent delta review verdict `READY_TO_REQUEST_BOUNDED_QUORUM_SURVIVAL_POC` as a contract-level readiness assessment, **NOT a PASS or permission already granted by PR #30**. Its five P0 findings G-P0-01..05 are `DESIGN_SPECIFIED` **only for an explicitly non-restored current 3-of-5 R majority and mandatory current independent verifier enforcement**; all underlying security properties remain `SECURITY_UNPROVEN / NOT_RUN`.

On Management's separate authority, **authorize S0-09H only** as a disposable bounded implementation experiment of an **actual durable replicated ordered quorum journal** under surviving non-restored majority. This is not authorization for a general Lane2 root, W disaster recovery, production consensus architecture, KMS/HA/credential/vendor selection, or any physical/admin-domain protection claim. If the implementation is merely an assumed oracle, five wrappers, fake leader, single-database log or unverified majority counter, it **does not meet the novelty threshold** over S0-09F and cannot satisfy this task.

## Exact supported scope (hypothesis, not proven fact)

1. Five currently admitted R voting members in the defined test configuration, using a real algorithm and durable log. A current **non-restored voting majority remains healthy and preserves the committed history** through all **supported** W and minority-R restoration tests; quorum-safety, current reads and correct member reconfiguration must be observed, not assumed from three healthy responses.
2. **W** may be restored from e1 after a majority-committed e2/B takeover. Up to a minority of R members may be restored **only as nonvoting quarantined learners**, catching up to the actual authenticated committed head before possible re-admission; never restore a voter’s term/vote/log and silently resume voting under its old credential.
3. Mandatory **independently admitted current verifier/guard policy** must deny every stale/old endpoint (direct SQL, issuer, RLS, PgBouncer reused backend, old local C-only/legacy route and restored W); a new verifier service alone is not enough if any old route still authorizes. This is a **preflight stop condition**, not a soft risk.
4. Current root/head, owner/policy, durable OPEN and UNKNOWN, idempotency keys, replay/compaction state and key retirement must be tied to the **same majority-committed log index** before any permit; a scalar epoch and W-only journal are insufficient.
5. `FIRST_USE_GRANTED` and `REVOKE_INTENT` have a durable total order. If an old grant precedes revoke, that old local transaction may still commit **while the successor stays NOT_READY**. A later first use is denied; successor READY waits for *positively proven* durable local outcome and ordered CLOSE. A signed nonce is not an instantaneous revocation mechanism.
6. `OPEN_UNKNOWN` and `FENCED_UNRESOLVED` cannot become closed/READY on physical hard fence, timeout, absence of a backend, operator signature or fixture reset. Lane3 remains `BLOCKED / NOT_RUN`.
7. A **responsive but coherently rewound majority** is categorically **outside** the supported envelope even with a current verifier: no surviving head means a fresh old-history response need not be detectable. Majority/root rollback, all-member loss, copied physical root/actor credentials, malicious DB superuser and shared privileged custody remain **P0 unproven**; conservative global denial is a requirement *only where surviving mandatory enforcement is actually demonstrable*, not a claimed universal detector.

## Proof and safe-stop gates

- **Preflight:** verify actual PR #27 head `2bebe0022956809b3842a015d215e6332c5a8b0f` (or report change and reassess) and pin designs by SHA. New branch `work/s0-09h-quorum-survival-poc`, stacked **Draft** PR on `work/s0-09f-w-oracle-deny-only-poc`, not main. Keep all previous Draft PRs including #30 unmerged/unmodified.
- **Healthy positives before faults:** real scoped old/new issuer, SQL/RLS and PgBouncer operations with admitted actors and current quorum, exact names/ids, backend/xid and log index. No vacuous negative test from missing grants/invalid arguments.
- **Actual restore and quorum:** current majority, committed e2, old W e1 restoration, minority learner recovery, log-prefix/head/full OPEN replay, signer and manifest retirement, lost acknowledged/ambiguous R commit and stale signed reads. Use real protocol-level behavior; prove source/test sensitivity by disabling a single check for **reason-specific mutation RED**, then byte-identical restoration and original assertion GREEN.
- **Commit/takeover cuts:** durable R OPEN before permit, grant/revoke order, old in-flight transaction commit vs successor readiness, unknown local outcome. Include **pre-ABORT**, lost ABORT and lost CLOSE ACK cuts if actually executable; mark NOT_RUN if not, never imply lifecycle exhaustive coverage. Prepared transactions remain prohibited and tested unless explicitly modeled.
- **Negative controls:** quorum loss, old signer or verifier, old pooled/direct DB access, missing/incomplete checkpoint, stale idempotency response and incomplete replay must yield true fail-closed. **Any old-owner fresh issuance/RLS after supported restore; forgotten OPEN; old transaction commit while successor ready; old verifier bypass; unsafe vote/rebootstrap; or UNKNOWN auto-clear => P0 FAIL_SECURITY**, not a harmless CI SUCCESS.
- **Regression and provenance:** preserve 129 previously distinct inherited +40 assumed-W F cases across their own suites. Keep original unchanged S0-09D C-only `test_anchor_rollback_must_not_revive_previous_owner` and the historical **FAIL_SECURITY** result. New Q-backed regression has a new name; GREEN there does not repair legacy D.
- **Output:** pinned reproducible actual versions, declared test failure domains/custody limits, exact SHA Push and PR merge-ref CI logs and artifacts, number of *new distinct* Q methods, expected RED/real GREEN/FAIL/NOT_RUN matrix, independent read-only final reviewer, independent Management vote. No PASS from a forced “W continuity lost” flag or stubbed majority.
- **STOP immediately** if mandatory current guard cannot cover all endpoints, if actual durable quorum/journal cannot be built, if restored minority can vote or old authority revives, if unknown OPEN loses its hold or a root can be re-genesis’d from old copies. Report the observed failure and preserve the test.

## Unchanged architecture gates

- **S0-09D:** original C anchor epoch2→1 rollback remains `FAIL_SECURITY`; old A regained fresh issuance and scoped RLS. S0-09F's W-oracle path proved only conditional integration. 129+40=169 previous distinct cases are **not real R anti-rollback proof**.
- **Lane2 real-root majority rollback / independent physical custody / shared control plane:** `BLOCKED / NOT_RUN`. Only the **Q-survival slice** of a real replicated log is authorized as an experiment. No auto recovery of lost majority, physical PITR/clone guarantee, production HA or approved signing-key lifecycle.
- **Lane3 orphan OPEN resolution:** `BLOCKED / NOT_RUN`. Any UNKNOWN can produce indefinite safe downtime; cannot be cleared to satisfy CI.
- [S0-09G Issue #28](https://github.com/alireza-anari/cac-project/issues/28), [parent #23](https://github.com/alireza-anari/cac-project/issues/23), [Architecture baseline #9](https://github.com/alireza-anari/cac-project/issues/9) remain **OPEN**; [SOURCE-001 #1](https://github.com/alireza-anari/cac-project/issues/1) / `GATE-SOURCE` remain **BLOCKED**. No promotion of `NEW_BASELINE_ACCEPTED`, APR-033/034/035/036 change, identity/onboarding, Production or Sprint0 approval. All previous Draft PRs remain Draft/unmerged.

**Management vote:** `Q_SURVIVAL_IMPLEMENTATION_POC_AUTHORIZED_WITH_LIMITS / REAL_R_ROOT_SECURITY_UNPROVEN / FULL_LANE2_AND_LANE3_BLOCKED`. This vote authorizes executing the narrowly specified defensive test, **not accepting its results in advance**.
