# CAC — S0-09C Architecture Review Decision

**Decision date:** 2026-11-05  
**Role:** Astra Management / CAC Architecture  
**Reviewed implementation SHA:** `3a1138885a5c73e0b427a25b858fa399ff56cd24`  
**Final evidence/documentation SHA:** `8bd81906f6edbf1732e22c46ca8925c7dec1a595`  
**Stacked Draft PR:** [#20](https://github.com/alireza-anari/cac-project/pull/20), base `work/s0-09b-issuer-pool-recovery-poc` at `75be54d0f18d6391014ca4e5d91466d62a6cf72c`  
**Disposition:** `EVIDENCE_HANDOFF_ACCEPTED_WITH_LIMITS / RECOVERY_PROTOCOL_ACCEPTANCE_DEFERRED / NEW_IMPLEMENTATION_EXPERIMENTAL / NOT_MERGED`  
**Architecture baseline gate:** [#9](https://github.com/alireza-anari/cac-project/issues/9) remains OPEN.  
**Historical source:** [SOURCE-001 #1](https://github.com/alireza-anari/cac-project/issues/1) and `GATE-SOURCE` remain BLOCKED.

## Executive ruling

**Accept the S0-09C bounded synthetic proof/evidence handoff, but DEFER ratification of the recovery-generation fencing architecture and the wider trusted-context protocol.** Green regression runs are not equivalent to proof under untested candidate mutations, merged C+pool behavior, anti-rollback infrastructure and operational orphan recovery.

This ruling does **not** authorize merge of any experimental PR (#11, #16, #18, #20), publication to production, canonical source-baseline acceptance, identity/MFA/CSRF integration, onboarding, a KMS/HA design, or Sprint 0 completion. The original approved APR-033/034/035/036 requirements are unchanged.

## Evidence reviewed

- [S0-09C handoff](https://github.com/alireza-anari/cac-project/blob/8bd81906f6edbf1732e22c46ca8925c7dec1a595/docs/S0_09C_HANDOFF.md), [separate read-only security review](https://github.com/alireza-anari/cac-project/blob/8bd81906f6edbf1732e22c46ca8925c7dec1a595/docs/security/S0_09C_READ_ONLY_REVIEW.md), [proposed CR/ADR](https://github.com/alireza-anari/cac-project/blob/8bd81906f6edbf1732e22c46ca8925c7dec1a595/docs/changes/CR-S0-09C-001-recovery-fencing-evidence.md) and [evidence manifest](https://github.com/alireza-anari/cac-project/blob/8bd81906f6edbf1732e22c46ca8925c7dec1a595/docs/evidence/S0_09C_CI.json).
- The final two commits change documentation only: all executable implementation evidence is pinned to `3a1138885a5c73e0b427a25b858fa399ff56cd24`. Synthetic PR runs at final doc head checked out GitHub merge-ref `bb6ae984ef9a33762dda0f927fca00c9e15697aa` against unchanged base; prior exact-implementation Push CI remains separately recorded. The evidence manifest's artifact digests are GitHub metadata, **not independently recomputed ZIP hashes**.
- Actual final documentation-head [S0-09C PR run 42052172024](https://github.com/alireza-anari/cac-project/actions/runs/42052172024): SUCCESS, 20 distinct S0-09C tests before and after S0-09C rollback/reapply, zero error/skip/failure in each final green run, expected parent unsafe-restore RED, bounded structural roundtrip PASS.
- Actual final documentation-head [full backend PR run 42052172261](https://github.com/alireza-anari/cac-project/actions/runs/42052172261): SUCCESS, 43 foundation cases (39 PostgreSQL + four configuration subprocess), 24 S0-09A PostgreSQL cases, 27 S0-09B cases; each cohort twice around its rollback/reapply, nonowner Django ORM PASS, independent documented RED sensitivity controls.
- [Focused S0-09B PR run 42052172656](https://github.com/alireza-anari/cac-project/actions/runs/42052172656): SUCCESS, 27 separate B cases. **114 distinct cases across separate workflows** is an inventory, not a single 114-case test invocation nor 228 distinct tests.
- Previous exact implementation SHA Push runs [S0-09C 42046511769](https://github.com/alireza-anari/cac-project/actions/runs/42046511769) and [full backend 42046511716](https://github.com/alireza-anari/cac-project/actions/runs/42046511716) also PASS. The corrected `test_missing_bootstrap_and_wrong_acl_never_ready` uses *effective* unsafe function EXECUTE privileges and missing local config, rather than presuming that a direct REVOKE removes all inherited privileges.
- PostgreSQL 17.11 on three separately initialized logical instances A, B, C (single CI host), with PgBouncer 1.22.0 used by inherited B tests. No independent Management database rerun; source/log review is not external certification.
- The separate reviewer found **three Medium and two Low evidence/coverage findings** and identified no new exploitable bypass within the declared trusted broker/guard/admin/non-rolled-back-anchor assumptions. This is not a general vulnerability absence claim.

## Accepted synthetic observations — tightly bounded

1. Three separately initialized PostgreSQL clusters have distinct system identifiers; a third **non-restored** anchor C was held outside the application logical restore. Its monotonic CAS reservation, epoch/owner/phase, signed committed-reader ACK and online checks denied the tested restored B and stale A until a current valid activation.
2. A restored copy of local ready state and issuance ledger alone does not mint current authority when the external anchor is healthy. Already active A becomes unready after B's takeover in the observed sequential schedule; a basic two-thread reservation has a single winner. This is **not exhaustive split-brain/consensus proof**.
3. The test's committed OPEN intent blocks takeover while an operation is unresolved. **Healthy live OPEN gates permit concurrent same-owner work; an orphan OPEN blocks readiness/new guarded use and can cause indefinite safe downtime**. The fixture reset is *not* an approved incident-reconciliation procedure.
4. Missing mandatory local `fence_private.config` and an effectively unsafe `poc_private.issue_unfenced(...)` EXECUTE grant fail closed in the tested activation/readiness paths, including after activation. This does not prove a comprehensive installed-role/function integrity attestation.
5. Process exits, anchor SIGKILL/restart, lost local apply ACK, live old instance and defined rollback/savepoint cases were tested in bounded CI schedules; no packet-loss, standby routing, HA/quorum or real physical PITR is implied.

## Architecture decision: NOT YET RATIFIED

| Priority | Open obligation and present evidence gap |
|---|---|
| **P0** | No candidate-specific RED/GREEN mutation of C CAS monotonicity, online SQL fence and durable OPEN protection. Only the *parent unfenced restore* RED was executed for C. |
| **P0** | C wrappers were not exercised on the **same reused PgBouncer backend** across takeover, cancellation and rollback. Separate B pooling tests do not establish composition. |
| **P0** | C anchor itself may be rolled back/cloned or lose trusted endpoint/identity. This violates the monotonic independent-authority assumption. Current single-host three-cluster test is not a governed anti-rollback, quorum or HA contract. |
| **P0** | No externally witnessed safe reconciliation for orphan OPEN/ambiguous operation; indefinite fail-closed downtime may occur. Never automatically expire/clear OPEN solely to make the suite green. |
| **P1** | Wrong-endpoint/standby/read-only/transport and missing role/extension bootstrap fault matrix incomplete; wrong SID config is not actual endpoint substitution. |
| **P1** | Structural roundtrip and readiness/ACL predicates cover selected metadata, not every catalog property or privilege. |
| **P1** | Physical PITR/replica promotion, asymmetric network partition, deterministic heavy concurrent schedules, lost-response behavior, real credential lifecycle and production identity remain untested. |

Additional **unapproved product security contracts**: v2 canonical signed encoding, MAC comparison/cross-language interoperability, key custody/rotation/revocation, proof theft handling, production TTL/session/MFA policy, authorization audit and onboarding atomicity. No real identity or customer data entered this synthetic experiment.

## Governance and next test slice

- S0-09C is **accepted as a completed bounded evidence-delivery experiment only**. [Issue #19](https://github.com/alireza-anari/cac-project/issues/19) may be closed on that narrow basis, with this explicit scope disclaimer.
- The **unmet security proof obligations remain P0/P1**, tracked separately in [S0-09D Issue #21](https://github.com/alireza-anari/cac-project/issues/21). It authorizes only test-scoped experiments on a **new stacked Draft PR** targeting `work/s0-09c-recovery-fencing-poc`; it is **not** ratification of the proposed SQL protocol. The ability to physically fence an anchor rollback and safely reconcile orphan OPEN must be demonstrated, not inferred from a normal CI success.
- [CR-S0-09C-001](https://github.com/alireza-anari/cac-project/blob/8bd81906f6edbf1732e22c46ca8925c7dec1a595/docs/changes/CR-S0-09C-001-recovery-fencing-evidence.md) remains **PROPOSED**, not implemented or accepted as a production contract.
- Keep PRs [#11](https://github.com/alireza-anari/cac-project/pull/11), [#16](https://github.com/alireza-anari/cac-project/pull/16), [#18](https://github.com/alireza-anari/cac-project/pull/18), and [#20](https://github.com/alireza-anari/cac-project/pull/20) Draft/open/unmerged. Architecture baseline #9 OPEN; SOURCE-001/GATE-SOURCE BLOCKED.

**Final disposition:** `S0-09C_EVIDENCE_ACCEPTED_WITH_LIMITS / RECOVERY_ARCHITECTURE_DEFERRED / SOURCE_UNVERIFIED / NOT_MERGED`.
