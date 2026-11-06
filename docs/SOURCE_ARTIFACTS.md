# CAC — Source registry (historical and current)

> This is a declaration of evidence availability, not a source-integrity certificate for files not yet committed. Values below originate from the Project Sources v3.42 reference package and separate reported S0-03 delivery.

| Artifact | SHA-256 | Role / integration status |
|---|---|---|
| CAC Project Sources v3.42 ZIP | `c951e9656be6d35cf5b6a8b86129c5d80de5fd47c3bd0b7aeac446eba2271aa7` | Documentation/handoff bundle; exists in project context |
| v3.40 standalone onboarding ZIP | `e685e8872e953aff66daeeb6c551332f0dc6a178269f4041382c2f84c8e1118e` | Original independent Python/SQLite module; **not** integrated |
| v3.41 Work Handoff ZIP | `08316862c0afa60d500f7619dccaaee02ea92f60148111531e0f0aa6cee938bf` | Handoff documentation |
| SEC-REV-001 standalone corrected ZIP | `bdae7c4d6d146714bc0ef4a3e2d0280944c1ecf85560a491050fa427315ac39f` | S0-04: actual archive verified locally; exact corrected code/tests imported on Work branch |
| S0-03 handoff ZIP | `94f4d586023779500ea85a8cc7f76f092817e6b7da8a0dcb06aec2e59391a240` | S0-04: actual archive and manifest verified locally; conditional integration plans imported |
| v3.37 Architecture Freeze source | — | MISSING / SOURCE-001 BLOCKED |
| v3.38 Django Scaffold source | — | MISSING / SOURCE-001 BLOCKED |
| v3.39 PostgreSQL RLS source | — | MISSING / SOURCE-001 BLOCKED |

S0-04 verification: both archive hashes and internal manifests were checked from actual bytes. See `standalone/onboarding/PROVENANCE.json`. ZIP evidence bundles are not committed; selected source files are byte-identical to the verified corrected artifact.

## Correct provenance workflow

1. Obtain the authentic archive/reference.
2. Verify hash and internal manifest; record actual file set, provenance and publication scan.
3. Commit exact imported content to a branch, annotate whether historical/unpatched or corrected.
4. Connect build/test artifacts to a commit SHA and run clean-environment tests.
5. Keep `SOURCE-001` blocked until actual v3.37 source/reference is verified.

## Security remediation

A flaw in original standalone v3.40 `revoke_capability` was reported: a pending invitation could survive revoke if no active grant existed. The verified standalone fix contains **13 added + 32 original passing tests**, and remains **NOT_MERGED / SOURCE_UNVERIFIED**, and PostgreSQL accept/revoke race tests were designed but NOT EXECUTED.

Do not describe the original v3.40 source as the corrected security release.

## Historical bootstrap status — before S0-04

- Eight original `v3.42` core governance documents were imported to `main` under `docs/cac/`, verified byte-for-byte against the project ZIP.
- Seven reference source/test/OpenAPI blobs from the **original unpatched v3.40** archive were imported byte-for-byte on `archive/v3.40-unpatched-reference` under `reference/v3.40-unpatched/`.
- The corrected S0-02 and final S0-03 Library links are **not** equivalent to locally accessible archive bytes; those corrected artifacts have **not** yet been imported to GitHub.
- Source recovery issue: https://github.com/alireza-anari/cac-project/issues/1
- Corrected security handoff issue: https://github.com/alireza-anari/cac-project/issues/2

## S0-04 verified import — 2026-10-27

- Base main: `16ffff85f07d1464103f2e81769696e2ee28f612`.
- Historical branch commit: `0923d9bd761e04ba5bcf83c37e91ef7332f64c64`; all seven reference blobs compared with actual original v3.40 archive and matched.
- Source ID: `CAC-SEC-REV-001-STANDALONE-S0-02`; no fallback reconstruction used.
- Branch: `work/sec-rev-001-standalone-import`; selected exact source under `standalone/onboarding/`. Packaging and README are new import metadata, not historical bytes.
- Real clean-venv installation/import and 45 unittest results: [evidence](evidence/s0-04/execution.json). CI is tracked by actual commit/run checks, not inferred from these local results.
- v3.37/v3.38/v3.39 remain MISSING. SOURCE-001 stays BLOCKED.

## Repository acceptance update — 2026-10-28

PR [#3](https://github.com/alireza-anari/cac-project/pull/3) was reviewed and merged on main with squash commit `a6f7818bb4b2bfa0db24d5007dcc924bfaeaf8ed`. Only independent standalone code/test/evidence artifacts were imported. The Work-reported S0-02/S0-03 archive SHA-256 values remain provenance records; GitHub does not prove the authentic v3.37 source has been recovered. Current status is `MERGED_TO_REPOSITORY / NOT_INTEGRATED / SOURCE_UNVERIFIED`; full integration gates remain BLOCKED.

## S0-06 — renewed source recovery audit

See [S0-06 provenance report](S0_06_SOURCE_RECOVERY.md). All five advertised branch histories and current accessible ZIP bytes were rechecked: 38 commits, 82 blobs, six unique archives, 257 matching manifest entries. No authentic v3.37/v3.38/v3.39 source recovered; SOURCE-001 remains BLOCKED. Exact searches, exclusions and unavailable conversation-file leads are recorded separately from verified byte sources. No original archive is published by this audit.

## S0-06 merge and new-origin contingency — 2026-10-28

The reviewed, docs/audit-only source inventory was merged via [PR #8](https://github.com/alireza-anari/cac-project/pull/8), squash commit `43b5a0888723d621bad2722a74ce9b8a37825666`. It establishes no authentic original v3.37/v3.38/v3.39 implementation and does not clear `SOURCE-001`.

[ARCH-BASELINE-001 #9](https://github.com/alireza-anari/cac-project/issues/9) proposes an explicitly separate **new implementation** strategy requiring an Architecture ruling before canonical baseline promotion. [S0-07 #10](https://github.com/alireza-anari/cac-project/issues/10) scopes only an isolated exploratory Django/PostgreSQL prototype. Any such work must retain `NEW_IMPLEMENTATION_EXPERIMENTAL` provenance, never be called a recovered historical source, and cannot pass the historical source gate.

## S0-07 new-origin experimental source — Management review 2026-10-29

- Source ID: `CAC-NEW-ORIGIN-S0-07`; status: `NEW_IMPLEMENTATION_EXPERIMENTAL`. Implementation branch `work/s0-07-new-origin-backend-foundation`; current PR head `ba8a2d8ce0aa0dc825b2a55c02f7f6d5c9278e16`; base `main` inspected at `025931e0a612ff95c8165dec7c82af0d922b181a`. See [Draft PR #11](https://github.com/alireza-anari/cac-project/pull/11) and [handoff](https://github.com/alireza-anari/cac-project/blob/ba8a2d8ce0aa0dc825b2a55c02f7f6d5c9278e16/docs/S0_07_HANDOFF.md).
- Architecture ruling approved continuing isolated experimentation only; no canonical baseline, no merge/promotion and no historical provenance claim. [#9](https://github.com/alireza-anari/cac-project/issues/9) remains open as baseline acceptance gate.
- Actual CI success at exact head: [push run 40922077422](https://github.com/alireza-anari/cac-project/actions/runs/40922077422); [PR synthetic-merge run 40922090129](https://github.com/alireza-anari/cac-project/actions/runs/40922090129). Work reports 32 distinct PostgreSQL tests executed twice with rollback/reapply, plus Django check, migration drift and nonowner ORM checks.
- Management follow-up: [S0-07 security issue #12](https://github.com/alireza-anari/cac-project/issues/12). Open gaps include direct grant-to-other-principal regression, signed malformed-claim and max-TTL tests, function privilege regression, and fail-closed secret configuration. Real issuer/key custody, MFA/CSRF/session revocation, pooling, onboarding concurrency/audit remain future gates.
- This source is **new code**, not recovered or reconstructed v3.37/v3.38/v3.39. `SOURCE-001 / GATE-SOURCE` remains **BLOCKED** and this experiment cannot clear it.


## S0-07B experimental branch hardening — 2026-10-30

- Current unmerged [Draft PR #11](https://github.com/alireza-anari/cac-project/pull/11) head `a27eab0e978c6c60d54fab45b9f467ebd7ddff56`; historical provenance remains **new-origin experimental only**, never recovered v3.37/v3.38/v3.39.
- Management verified final-head [push CI 40925350556](https://github.com/alireza-anari/cac-project/actions/runs/40925350556) and [PR synthetic-merge CI 40925362772](https://github.com/alireza-anari/cac-project/actions/runs/40925362772); 43 distinct tests twice, role-scoped negative tests, 3 deliberately weakened security controls detected, rollback/reapply equality and nonowner ORM PASS. 39 are PostgreSQL authorization tests; 4 are configuration subprocess tests.
- [S0-07B handoff at exact head](https://github.com/alireza-anari/cac-project/blob/a27eab0e978c6c60d54fab45b9f467ebd7ddff56/docs/S0_07B_HANDOFF.md). Security regression follow-up [#12](https://github.com/alireza-anari/cac-project/issues/12) is completed in narrow scope; review recorded on PR #11.
- **No merge to main, no accepted canonical backend baseline**. [#9](https://github.com/alireza-anari/cac-project/issues/9) remains the architecture acceptance gate; [S0-08 #13](https://github.com/alireza-anari/cac-project/issues/13) is a docs-only trusted-identity/context/onboarding architecture mission. Historical `SOURCE-001 / GATE-SOURCE` remains BLOCKED.


## S0-08 governance-only source record — 2026-10-30

- The reviewed docs-only [PR #14](https://github.com/alireza-anari/cac-project/pull/14) was merged at `b0fdfad80a7ccc470a70cf3ed855b18282dc7dda`. Content: eight `docs/s0-08/` Markdown design files, **not executable product source**, no migration/API/schema change.
- The authoritative [scoped S0-08 Architecture decision](architecture/S0_08_ARCHITECTURE_RULING.md) approves only the stated experimental directions/invariants; the S0-08 proposals are not automatically canonical contracts. A synthetic test-only protocol evaluation is tracked at [#15](https://github.com/alireza-anari/cac-project/issues/15).
- Historical `v3.37/v3.38/v3.39` source is still unrecovered; new-origin experimental PR #11 remains Draft and unmerged. `SOURCE-001 / GATE-SOURCE` remains BLOCKED, `NEW_BASELINE_ACCEPTED` is **not** granted, and no deployment is authorized.


## S0-09A synthetic PoC provenance — Management review 2026-11-03

- Source remains `CAC-NEW-ORIGIN-S0-07 / NEW_IMPLEMENTATION_EXPERIMENTAL`; new `experimental/backend/context_poc/` code in [stacked Draft PR #16](https://github.com/alireza-anari/cac-project/pull/16) at `f351e26aa93ec87f17366dbaff85a87b171d36d2`, based on [Draft PR #11](https://github.com/alireza-anari/cac-project/pull/11) head `a27eab0e978c6c60d54fab45b9f467ebd7ddff56`. This branch is **NOT merged**. The contents are synthetic PostgreSQL PoC code, **not recovered historical v3.37/v3.38/v3.39 source**.
- [Architecture ruling](architecture/S0_09A_ARCHITECTURE_RULING.md) records `EXPERIMENT_ACCEPTED_WITH_LIMITS / PROTOCOL_PROPOSED`, not product identity/key/issuer/ledger contract approval. GitHub final-head [Push CI](https://github.com/alireza-anari/cac-project/actions/runs/41578052301) and [PR CI](https://github.com/alireza-anari/cac-project/actions/runs/41578057672) passed 43 inherited + 24 new tests twice each, independent SQL schema/ACL/RLS roundtrip and synthetic negative tests. No Management local independent PostgreSQL rerun.
- Execution [#15](https://github.com/alireza-anari/cac-project/issues/15) closed strictly as experimental handoff. Follow-up [#17](https://github.com/alireza-anari/cac-project/issues/17) remains a separate synthetic proof gate for process isolation, actual pool/recovery/timing tests. Historical `SOURCE-001 / GATE-SOURCE` remains **BLOCKED**, canonical `NEW_BASELINE_ACCEPTED` is **not granted** and [#9](https://github.com/alireza-anari/cac-project/issues/9) remains OPEN.


## S0-09B synthetic process/pool/recovery provenance — Management review 2026-11-03

- [S0-09B PR #18](https://github.com/alireza-anari/cac-project/pull/18), exact head `75be54d0f18d6391014ca4e5d91466d62a6cf72c`, is stacked on [S0-09A PR #16](https://github.com/alireza-anari/cac-project/pull/16) branch at `f351e26aa93ec87f17366dbaff85a87b171d36d2`; it remains Draft/unmerged. No changes to PR #11/#16. Source identity remains `CAC-NEW-ORIGIN-S0-07 / NEW_IMPLEMENTATION_EXPERIMENTAL`; no historical v3.37/v3.38/v3.39 source is recovered.
- [Official architecture ruling](architecture/S0_09B_ARCHITECTURE_RULING.md): `EXPERIMENT_ACCEPTED_WITH_LIMITS / PROTOCOL_PROPOSED`. [Issue #17](https://github.com/alireza-anari/cac-project/issues/17) closed strictly as completed synthetic experiment.
- Final-head full Push [41584962736](https://github.com/alireza-anari/cac-project/actions/runs/41584962736), PR synthetic merge [41584967557](https://github.com/alireza-anari/cac-project/actions/runs/41584967557), focused Push [41584962878](https://github.com/alireza-anari/cac-project/actions/runs/41584962878) and focused PR [41584967696](https://github.com/alireza-anari/cac-project/actions/runs/41584967696) all SUCCESS. Full runs pass the unchanged 43+24 inherited floor and 27 new S0-09B cases before/after rollback/reapply (94 distinct cases). PostgreSQL 17.11 / PgBouncer 1.22.0 / Python 3.12.15 / Django 5.2.18 / psycopg 3.3.6. No independent local management database rerun or final external security certification.
- Process separation is bounded to same-host Linux UIDs and kernel peer credentials; pooling to pinned local PgBouncer transaction mode and bounded schedules. Restart and same-cluster logical restore are proven only as described in handoff. **Restore without independent generation fencing is a reproduced P0 replay risk**: manual generation change rejects old authority, but automatic durable fencing/readiness/split-brain control is absent. Key custody, bearer-proof theft, canonical v2 and constant-time MAC, PITR/HA remain P0 open; revocation wait/admission/DoS and broader pool operations remain P1.
- [S0-09C Issue #19](https://github.com/alireza-anari/cac-project/issues/19) authorized for synthetic fail-closed generation fencing/split-brain proof on a new stacked Draft PR. Historical `SOURCE-001 / GATE-SOURCE` remains BLOCKED, canonical `NEW_BASELINE_ACCEPTED` not granted, [Gate #9](https://github.com/alireza-anari/cac-project/issues/9) OPEN.


## S0-09C provenance and management decision — 2026-11-05

- New-origin experimental code remains in [Draft stacked PR #20](https://github.com/alireza-anari/cac-project/pull/20), `work/s0-09c-recovery-fencing-poc`, final docs head `8bd81906f6edbf1732e22c46ca8925c7dec1a595`; underlying tested implementation `3a1138885a5c73e0b427a25b858fa399ff56cd24`. **No code merge to main**. PRs #11/#16/#18/#20 remain Draft/unmerged. Identity `CAC-NEW-ORIGIN-S0-07 / NEW_IMPLEMENTATION_EXPERIMENTAL`, not recovered v3.37/v3.38/v3.39.
- [Formal decision](architecture/S0_09C_ARCHITECTURE_RULING.md): `EVIDENCE_HANDOFF_ACCEPTED_WITH_LIMITS / RECOVERY_ARCHITECTURE_DEFERRED / PROTOCOL_PROPOSED`. [Final technical handoff](https://github.com/alireza-anari/cac-project/blob/8bd81906f6edbf1732e22c46ca8925c7dec1a595/docs/S0_09C_HANDOFF.md), independent read-only review and proposed CR reside only in the stacked experimental branch. [Issue #19](https://github.com/alireza-anari/cac-project/issues/19) closed strictly as a **bounded synthetic evidence-delivery task**, not full security acceptance.
- Actual final doc-head synthetic PR CI [S0-09C](https://github.com/alireza-anari/cac-project/actions/runs/42052172024), [full inherited backend](https://github.com/alireza-anari/cac-project/actions/runs/42052172261), and [S0-09B focused](https://github.com/alireza-anari/cac-project/actions/runs/42052172656) all SUCCESS; 114 distinct cases across separate workflows, each applicable cohort repeated around structural rollback/reapply. No independent Management PostgreSQL rerun or production certification.
- Remaining P0 obligations in [S0-09D #21](https://github.com/alireza-anari/cac-project/issues/21): candidate-specific C CAS/SQL fence/OPEN sensitivity, combined C+PgBouncer reuse, anchor rollback/identity, and orphan OPEN recovery. The non-restored anchor is on the same CI host; no physical PITR/quorum/HA and no external key custody contract. Original `SOURCE-001 / GATE-SOURCE` BLOCKED; [Architecture gate #9](https://github.com/alireza-anari/cac-project/issues/9) OPEN. No canonical new baseline or production.


## S0-09D/E/F new-origin evidence provenance checkpoint — 2026-11-06

- All work remains `CAC-NEW-ORIGIN-S0-07 / NEW_IMPLEMENTATION_EXPERIMENTAL / PROTOCOL_PROPOSED`, **not recovered historical CAC source**. [Draft D PR #22](https://github.com/alireza-anari/cac-project/pull/22) final head `ca043e2751ea1dbcb7aed3c1ed3d171a9bb1f0e2` records real C anchor epoch2→1 rollback reactivating old owner A and enabling fresh issuance/scoped RLS: **`FAIL_SECURITY`**. D's evidence acceptance is not recovery-protocol ratification. [S0-09D formal ruling](architecture/S0_09D_ARCHITECTURE_RULING.md).
- [S0-09E design proposal](architecture/S0_09E_ANTI_ROLLBACK_DESIGN_PROPOSAL.md), [targeted R1 refinement](architecture/S0_09E_TARGETED_DESIGN_REFINEMENT_R1.md), and [Lane1-only authorization](architecture/S0_09E_LANE1_SCOPED_AUTHORIZATION.md) remain **proposed contract / limited experiment authorization only**. Independent read-only reports are in separate unmerged Draft PRs [#24](https://github.com/alireza-anari/cac-project/pull/24) and [#25](https://github.com/alireza-anari/cac-project/pull/25). The four original P0 security proof obligations are not discharged by their contractual scope refinements.
- [Draft S0-09F PR #27](https://github.com/alireza-anari/cac-project/pull/27), branch `work/s0-09f-w-oracle-deny-only-poc`, final head `2bebe0022956809b3842a015d215e6332c5a8b0f`, executable proof head `168543a32a937c56113c1b51b26b2fb82af17257` with one documentation-only follow-up. [Technical handoff](https://github.com/alireza-anari/cac-project/blob/2bebe0022956809b3842a015d215e6332c5a8b0f/docs/S0_09F_HANDOFF.md), [independent automated review](https://github.com/alireza-anari/cac-project/blob/2bebe0022956809b3842a015d215e6332c5a8b0f/docs/security/S0_09F_READ_ONLY_REVIEW.md), and [formal ruling](architecture/S0_09F_ARCHITECTURE_RULING.md) accept only `INTEGRATION_PROVEN_ONLY_UNDER_ASSUMED_W`. All eight final-head CI workflows SUCCESS, 129 separate inherited +40 new distinct GREEN across cohorts; three targeted mutation RED/restored GREEN probes. Legacy D C-only rollback is still separate `FAIL_SECURITY` and not counted as GREEN.
- The W oracle is a fourth independently initialized PostgreSQL cluster **on one CI host** with assumed trusted control/monotonic state. This does **not** prove real W own-restore irreversibility, infrastructure/key custody, physical same-identity clones, HA/PITR or safe orphan OPEN release; Lane2/Lane3 `BLOCKED / NOT_RUN`. Specifically pre-ABORT and lost ABORT/CLOSE acknowledgment fault cuts remain `NOT_RUN`.
- Execution [#26](https://github.com/alireza-anari/cac-project/issues/26) closed **only** as completed bounded evidence. Architecture [#23](https://github.com/alireza-anari/cac-project/issues/23) stays P0 OPEN, [S0-09G #28](https://github.com/alireza-anari/cac-project/issues/28) is **DESIGN-FIRST, not implementation permission**. PRs #11/#16/#18/#20/#22/#24/#25/#27 all Draft/open/unmerged, no experimental code merge into main. `SOURCE-001 / GATE-SOURCE` BLOCKED, [baseline #9](https://github.com/alireza-anari/cac-project/issues/9) OPEN, no canonical-source, Production, Sprint0 or trusted-context-protocol approval.


## S0-09G design-only provenance — 2026-11-06

- [S0-09G root-continuity R0](architecture/S0_09G_REAL_W_ROOT_DESIGN_CANDIDATE_R0.md) is an Astra Management **proposal** added on `main` as new-origin **documentation only**; [Issue #28](https://github.com/alireza-anari/cac-project/issues/28) is OPEN/P0 and requests **independent read-only architecture review**, not implementation. It is not recovered historical CAC v3.37/v3.38/v3.39 or evidence that a real root has been built.
- R0 compares an independently governed linearizable nonrollback R, an externally sealed monotonic identity/counter alternative, immutable audit evidence only and permanent fail-closed pause. R's actual own rollback/restore, signing/verifier policy, custody/actor clone, complete OPEN retention and cross-database outcome safety remain `PROPOSED / P0 BLOCKED / NOT_RUN`; no vendor/technology or protocol acceptance.
- [S0-09D Draft #22](https://github.com/alireza-anari/cac-project/pull/22) retains `FAIL_SECURITY` for legacy C anchor epoch rollback. [S0-09F Draft #27](https://github.com/alireza-anari/cac-project/pull/27) under `W_ORACLE_ASSUMED` has accepted **bounded conditional evidence only** (129 inherited +40 distinct new GREEN across separate workflows); no executable R/W-root implementation entered main. Lane3 orphan clearing BLOCKED. Prior Draft PRs #11/#16/#18/#20/#22/#24/#25/#27 remain unmerged.
- `SOURCE-001 / GATE-SOURCE = BLOCKED`, [baseline #9](https://github.com/alireza-anari/cac-project/issues/9) OPEN, [architecture #23](https://github.com/alireza-anari/cac-project/issues/23) OPEN; no original source recovery, source-baseline promotion, production or Sprint0 approval.


## S0-09G R1 design-only provenance and security-gate record — 2026-11-06

- Independent [R0 read-only review](https://github.com/alireza-anari/cac-project/blob/e63b16a0916aa6a43d5a36a20027dab20b506464/docs/security/S0_09G_ROOT_DESIGN_READ_ONLY_REVIEW.md) is one **unmerged documentation-only** addition in [Draft PR #29](https://github.com/alireza-anari/cac-project/pull/29), at `e63b16a0916aa6a43d5a36a20027dab20b506464`. Findings: five P0 design gaps, 3 P1 and 1 P2; `TARGETED_DESIGN_REFINEMENT_REQUIRED`. No R code or test execution, no independent physical root verification.
- Manager-authored [S0-09G targeted R1](architecture/S0_09G_TARGETED_ROOT_REFINEMENT_R1.md), first commit `c77f994a8049f2ff1cba040814c60a03a4651cb4`, is **new-origin architecture documentation**, not recovered CAC v3.37-v3.39. It proposes *only* a surviving non-restored 3-of-5 committed R majority and separately mandatory trusted verifier during W/minority-R restores. Complete OPEN/journal and head must be one ordered R commit; uncertain local outcomes block successors even after hard fencing. It does **not** prove or authorize R implementation or majority catastrophe recovery; jointly restored old verifier/root remains unsupported.
- Original [S0-09D](architecture/S0_09D_ARCHITECTURE_RULING.md) C-anchor rollback **FAIL_SECURITY** continues. [S0-09F](architecture/S0_09F_ARCHITECTURE_RULING.md) 169 distinct cases across separate workflows under assumed W are *not* evidence of real R nonrollback. All real R tests `NOT_RUN`; Lane2 implementation NOT_AUTHORIZED, Lane3 orphan OPEN release BLOCKED. [Issues #28](https://github.com/alireza-anari/cac-project/issues/28) and [#23](https://github.com/alireza-anari/cac-project/issues/23) OPEN P0; #9 OPEN; SOURCE-001/GATE-SOURCE BLOCKED; all previous Draft PRs including #29 unmerged. No canonical baseline or Production approval.
