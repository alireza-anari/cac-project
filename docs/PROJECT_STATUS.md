# CAC — Public Project Status

_Last updated: 2026-10-28. Management checked GitHub PR and CI logs; independent integrated security validation remains outstanding._

## Authorized architecture

The approved architectural baseline is **v3.37 / APR-036**. Preserved decisions include **APR-033**, **APR-034**, and **APR-035**. Architectural contract changes require a reviewed change request (CR).

## Source registry

| Source | Status |
| --- | --- |
| v3.37 approved baseline | Original source archive not recovered; **SOURCE-001 BLOCKED** |
| v3.38 / v3.39 | Original sources not recovered |
| v3.40 standalone onboarding | Referenced locally, **not integrated** |
| S0-02 security remediation | Standalone module merged to repository main via PR #3 at `a6f7818bb4b2bfa0db24d5007dcc924bfaeaf8ed`; **NOT_INTEGRATED / SOURCE_UNVERIFIED** |
| S0-03 evidence handoff | Archive/hash/manifest reported verified by Work; standalone handoff accepted for repository import by Management at PR #3 |
| S0-05 CI/contract tooling | Merged via PR #6 at `690505b3b622cb622865d0dfb8ef364bc1a6f119`; **tooling accepted only; CR-S0-05-001 pending** |
| v3.42 project sources | Governance/reference package, **not the complete product source** |

## Acceptance gates

| Gate | Status | Reason |
| --- | --- | --- |
| GATE-SOURCE | BLOCKED | The authentic baseline/repository ref is missing |
| GATE-BOOT | BLOCKED | No verified integrated bootstrap |
| GATE-MIG | BLOCKED | No verified Django/PostgreSQL migration run |
| GATE-TENANT | BLOCKED | No verified production-equivalent PostgreSQL/RLS isolation evidence |
| GATE-ONBOARD | BLOCKED | Integration and concurrency tests pending |

## Test-report boundaries

S0-04 executed **13 new + 32 original passing tests (45 total)** from this repository checkout in a fresh venv, plus installation and import outside the source tree. See [execution evidence](evidence/s0-04/execution.json). GitHub Actions result must be read from the actual PR/commit checks; local PASS alone is not CI PASS. PostgreSQL concurrency and full integration tests remain unexecuted.

## Planned workflow

1. Verify and recover the authentic source of truth without inventing a baseline.
2. Review independently delivered artifacts for secrets, licensing and sensitive content **before** any upload to this public repository.
3. Prepare a feature branch and reviewable pull request; never silently integrate against an unverifiable baseline.
4. Run clean-environment integration tests and resolve acceptance gates with actual commit-linked logs.

No production release is authorized by this record.

## Historical bootstrap import (before S0-04)

- Main branch contains the eight original core `docs/cac/00..07` v3.42 governance files. Each Git blob SHA was compared to the corresponding original file and **matched byte-for-byte**.
- Reference branch `archive/v3.40-unpatched-reference` contains an **unpatched, historical** Python/SQLite onboarding source snapshot and its tests/OpenAPI addendum. The seven core source/test/API blobs matched their original archive bytes.
- This branch is **not merged into main**, and must never be treated as the corrected `SEC-REV-001` handoff.
- Corrected S0-02 and S0-03 artifact ZIPs have not been fetched directly through this session; their **reported** hashes remain in Source Registry.
- `SOURCE-001` and all Django/PostgreSQL/RLS integration gates remain BLOCKED.

## S0-04 Work branch (historical record before merge)

Corrected artifact bytes and original reference branch were verified. Source lives under `standalone/onboarding/`; installation metadata and standalone-only GitHub Actions are added. See [handoff](S0_04_HANDOFF.md). This paragraph records the *pre-merge handoff*. PR #3 was subsequently merged into the GitHub repository on 2026-10-28; **no backend integration, migration or deployment** is claimed. SOURCE-001 and all integrated gates remain BLOCKED.

## Astra Management acceptance — 2026-10-28

- Reviewed [PR #3](https://github.com/alireza-anari/cac-project/pull/3), actual diff, original-vs-fixed revocation behavior, and GitHub Actions [run 40463377495](https://github.com/alireza-anari/cac-project/actions/runs/40463377495).
- Standalone package import accepted and merged via squash commit `a6f7818bb4b2bfa0db24d5007dcc924bfaeaf8ed`. No integrated backend was merged.
- CI evidence: Python 3.12.15, **45 tests passed**, package installed and out-of-tree import succeeded; synthetic PR merge was tested by CI. Job log was reviewed by Management.
- **Current source state: `MERGED_TO_REPOSITORY / NOT_INTEGRATED / SOURCE_UNVERIFIED`.**
- `SEC-REV-001`: **DONE for standalone scope only**. Historical tests are not a PostgreSQL concurrency, RLS, trusted IdP/MFA, CSRF or production security guarantee.
- `SOURCE-001` and `GATE-SOURCE / BOOT / MIG / TENANT / ONBOARD` remain **BLOCKED**; Sprint 0 is not complete; no Production release authorized.
- Follow-up work: source recovery; PostgreSQL concurrency and security gates; CI dependency pinning/maintenance.

## S0-05 Work — CI and standalone contract validation

A separate branch hardened Action/dependency pins and added OpenAPI 3.1.1 structural/lint checks and negative fixtures. Management reviewed the full PR diff and actual final-head CI logs, then accepted and merged PR #6 via squash commit `690505b3b622cb622865d0dfb8ef364bc1a6f119`. Final CI: 45 Python tests PASS, structural validation PASS, scoped lint 0 errors plus one visible `operation-4xx-response` warning, and 9 CLI fixtures PASS. [PR #6](https://github.com/alireza-anari/cac-project/pull/6) · [CI run](https://github.com/alireza-anari/cac-project/actions/runs/40713306009) · [handoff](S0_05_HANDOFF.md). `CR-S0-05-001` remains proposed, unapproved and unimplemented; no API semantics changed. SOURCE-001 and all integrated gates remain BLOCKED. This merge does not complete Sprint 0/1 or authorize production.

## S0-06 management acceptance — 2026-10-28

- Management reviewed [PR #8](https://github.com/alireza-anari/cac-project/pull/8), its 12 audit/report files, `tools/source-audit/{audit.py,compare.py}`, snapshot inventories and Work-provided exit/output evidence. Audit-only PR merged with squash commit `43b5a0888723d621bad2722a74ce9b8a37825666`.
- Scope: 5 branch histories (38 commits, 82 unique blobs, 61 historical paths), 10 ZIP paths (6 unique archives), ZIP CRC PASS and 257 matching manifest entries reported by Work; no v3.37/v3.38/v3.39 authenticated source was recovered. The audit commands were not independently rerun in an identical Work workspace by Management; this is a reviewed, scoped provenance handoff.
- **`S0-06 = DONE (audit only)`**. **`SOURCE-001 / GATE-SOURCE = BLOCKED`**. No application changes, new Django/PostgreSQL tests or production actions, and Sprint 0 is not complete.
- Stop repeat searches against unchanged sources without new leads. Maintain historical source recovery in [issue #1](https://github.com/alireza-anari/cac-project/issues/1).
- Parallel strategy: [ARCH-BASELINE-001 #9](https://github.com/alireza-anari/cac-project/issues/9) requests Architecture governance of a **new-origin**, clearly labeled implementation; [S0-07 #10](https://github.com/alireza-anari/cac-project/issues/10) scopes a test-only Django/PostgreSQL exploratory branch. **No new approved baseline exists** and no historical source gate is bypassed.

## S0-07 Management review and Architecture ruling — 2026-10-29

- Architecture ruling: **new-origin strategy approved for isolated experimentation only** as `CAC-NEW-ORIGIN-S0-07 / NEW_IMPLEMENTATION_EXPERIMENTAL`. No canonical baseline acceptance, no merge/promotion of PR #11, and no production integration. [ARCH-BASELINE-001 #9](https://github.com/alireza-anari/cac-project/issues/9) remains open as the canonical-baseline acceptance gate.
- Management inspected [Draft PR #11](https://github.com/alireza-anari/cac-project/pull/11), the handoff, 27 changed paths, proposed contract inventory, models/migrations, PostgreSQL role/RLS SQL, tests and workflow. Actual GitHub Actions results: [push run 40922077422](https://github.com/alireza-anari/cac-project/actions/runs/40922077422) and [PR run 40922090129](https://github.com/alireza-anari/cac-project/actions/runs/40922090129), both SUCCESS on head `ba8a2d8ce0aa0dc825b2a55c02f7f6d5c9278e16` (PR run tests GitHub synthetic merge).
- Reported evidence: 32 distinct real PostgreSQL tests, twice around rollback/reapply; Django checks and ORM under non-owner runtime; hash-locked dependencies and digest-pinned PostgreSQL service. These support the experimental proof only, not production security or historical compatibility.
- Management recorded a PR review comment (not approval) and opened [S0-07 security follow-up #12](https://github.com/alireza-anari/cac-project/issues/12): direct cross-principal grant regression, signed malformed mandatory-claim and max-TTL matrix, verifier/default function privilege checks, fail-closed Django secret configuration, and updated handoff evidence.
- **PR #11 remains Draft / unmerged.** Trusted issuer/key custody and rotation, real identity/MFA/CSRF/session revocation, pooling, provisioning/audit and accept/revoke races remain unresolved. Do not connect standalone onboarding or expose public API.
- `SOURCE-001 / GATE-SOURCE` remains **BLOCKED**; the new implementation does not clear historical recovery. Sprint 0 remains incomplete and no release is authorized.


## S0-07B management acceptance — 2026-10-30

- S0-07B regression/configuration hardening **ACCEPTED for the narrow experimental scope** at head `a27eab0e978c6c60d54fab45b9f467ebd7ddff56`; [Draft PR #11](https://github.com/alireza-anari/cac-project/pull/11) remains **OPEN / DRAFT / UNMERGED**.
- Management compared the new code with prior S0-07 head, inspected actual direct cross-principal grant, malformed signed-claim/TTL, function permission/default-privilege and fail-closed SECRET_KEY tests, synthetic weakness-detection harness, SQL roles and workflow.
- Actual GitHub Actions [push run 40925350556](https://github.com/alireza-anari/cac-project/actions/runs/40925350556) and [PR run 40925362772](https://github.com/alireza-anari/cac-project/actions/runs/40925362772) succeeded at exact head; latter tested a synthetic merge. Management read PR job log 123629299934: **43 distinct tests twice**, `ROUNDTRIP PASS`, actual nonowner `ORM PASS` and all three expected RED mutation regressions. Split: **39 PostgreSQL security tests + 4 configuration subprocess tests**; these are not 43 distinct PostgreSQL tests.
- [Security follow-up #12](https://github.com/alireza-anari/cac-project/issues/12) **CLOSED / COMPLETED** as narrowly scoped. No new independent product certification is implied.
- Historical `SOURCE-001 / GATE-SOURCE` stays **BLOCKED**. Architecture baseline acceptance [#9](https://github.com/alireza-anari/cac-project/issues/9) and S0-07 execution [#10](https://github.com/alireza-anari/cac-project/issues/10) remain open. Source remains `CAC-NEW-ORIGIN-S0-07 / NEW_IMPLEMENTATION_EXPERIMENTAL`.
- The next design-only workstream is [S0-08 #13](https://github.com/alireza-anari/cac-project/issues/13): trusted identity, issuer/key lifecycle, pool/transaction context and secure onboarding/accept-revoke contracts. No production integration, new canonical baseline or Sprint 0 completion has been approved.


## S0-08 architecture disposition — 2026-10-30

- Documentation-only [PR #14](https://github.com/alireza-anari/cac-project/pull/14), exact reviewed head `cad5e19a9351f00858da3c13b802a6125a78a30c`, was merged to `main` via `b0fdfad80a7ccc470a70cf3ed855b18282dc7dda`. Eight docs at `docs/s0-08/` are **DESIGN_ONLY / PROPOSED_CONTRACTS**, not implemented and not security-test PASS. [Execution #13](https://github.com/alireza-anari/cac-project/issues/13) closed as *documentation delivered*.
- [Architecture ruling](architecture/S0_08_ARCHITECTURE_RULING.md): conditional *directional* acceptance for server-side revocable identity/session, PostgreSQL guard/epoch/ordered transactions, least-privilege roles and SEC-REV-001 safety invariants. **No ratification** yet of cryptographic challenge/first-issuance ledger protocol, exact production session/MFA/TTL settings, SQL function interfaces, privacy retention, encrypted delivery or API status contract.
- Next [S0-09A #15](https://github.com/alireza-anari/cac-project/issues/15): limited synthetic, adversarial PostgreSQL proof-of-concept of issuer/challenge/savepoint and epoch boundary, on a **stacked Draft PR** against the existing experimental branch. No public HTTP/IdP/onboarding integration.
- [Architecture baseline gate #9](https://github.com/alireza-anari/cac-project/issues/9) remains **OPEN**; [experimental code PR #11](https://github.com/alireza-anari/cac-project/pull/11) remains **DRAFT / UNMERGED**. `SOURCE-001 / GATE-SOURCE = BLOCKED`; no Sprint 0/1 or production authorization.


## S0-09A Architecture acceptance (experimental only) — 2026-11-03

- Reviewed final-head [stacked Draft PR #16](https://github.com/alireza-anari/cac-project/pull/16), `f351e26aa93ec87f17366dbaff85a87b171d36d2`, targeting experimental `work/s0-07-new-origin-backend-foundation`. **PR #16 and PR #11 remain OPEN / DRAFT / UNMERGED.** No experimental backend code entered `main`.
- [Official scoped architecture ruling](architecture/S0_09A_ARCHITECTURE_RULING.md): `EXPERIMENT_ACCEPTED_WITH_LIMITS / PROTOCOL_PROPOSED`. [S0-09A Issue #15](https://github.com/alireza-anari/cac-project/issues/15) was CLOSED as a completed synthetic Proof of Concept, not as ratification of the identity protocol.
- Management checked [final-head push CI 41578052301](https://github.com/alireza-anari/cac-project/actions/runs/41578052301) and [final-head synthetic PR CI 41578057672](https://github.com/alireza-anari/cac-project/actions/runs/41578057672), each SUCCESS: **43 inherited (39 PostgreSQL + 4 config) and 24 new PostgreSQL tests**, each run before and after rollback/reapply; three deliberate RED weaknesses detected, prior NULL binding RED regression fixed; ORM/RLS/ACL/schema roundtrip and guarded lock witnesses PASS. This is GitHub Actions evidence, not a Management local database rerun.
- The v2 signed challenge, issuer DB login, independently committed first-issuance ledger, scope/epoch and savepoint defense demonstrate **bounded synthetic threat controls** only. No final protocol key custody, real issuer process, signed encoding, 5s/60s/120s timing policy, pool/failover/recovery, identity/MFA/CSRF or onboarding/audit/outbox integration approval.
- Follow-on [S0-09B Issue #17](https://github.com/alireza-anari/cac-project/issues/17) authorizes only process-isolated synthetic issuer and actual PgBouncer transaction-pool/recovery adversarial tests on a new stacked Draft PR; no product integration. [Architecture baseline gate #9](https://github.com/alireza-anari/cac-project/issues/9) remains **OPEN**. Historical [SOURCE-001 #1](https://github.com/alireza-anari/cac-project/issues/1) and `GATE-SOURCE` remain **BLOCKED**. Neither Sprint 0 nor Production is approved.


## S0-09B Architecture acceptance (experimental only) — 2026-11-03

- Reviewed exact stacked Draft [PR #18](https://github.com/alireza-anari/cac-project/pull/18) at `75be54d0f18d6391014ca4e5d91466d62a6cf72c`, base `work/s0-09a-trusted-context-poc` at `f351e26aa93ec87f17366dbaff85a87b171d36d2`. Eight commits / 19 files. PR #18 remains open, Draft and unmerged; PR #16 and #11 remain unchanged Draft/unmerged.
- [Official S0-09B Architecture ruling](architecture/S0_09B_ARCHITECTURE_RULING.md): `EXPERIMENT_ACCEPTED_WITH_LIMITS / PROTOCOL_PROPOSED`. [Issue #17](https://github.com/alireza-anari/cac-project/issues/17) CLOSED only as completed synthetic experiment/handoff; closure is not protocol ratification.
- Exact-head full Push [41584962736](https://github.com/alireza-anari/cac-project/actions/runs/41584962736) and full PR synthetic merge [41584967557](https://github.com/alireza-anari/cac-project/actions/runs/41584967557) both SUCCESS. Supplemental focused Push [41584962878](https://github.com/alireza-anari/cac-project/actions/runs/41584962878) and PR [41584967696](https://github.com/alireza-anari/cac-project/actions/runs/41584967696) also SUCCESS on same head. Each full run executes 43 inherited (39 PostgreSQL + 4 config), 24 S0-09A and 27 S0-09B cases, 94 distinct total, before and after rollback/reapply; each final green suite has zero failures/errors/skips. Three security-predicate REDs and one observer-control RED were expected, asserted, and restored.
- Real Linux UID/socket issuer separation, pinned PgBouncer 1.22.0 transaction pooling, backend PID/xid reuse, cancellation, rollback, concurrent scopes/revocation, controlled PostgreSQL restart, same-cluster logical restore, exact-clock and elapsed expiry/MFA checks passed within their documented scope. PostgreSQL 17.11, Python 3.12.15, Django 5.2.18, psycopg 3.3.6.
- **P0 integration blocker demonstrated:** logical restore of keys+generation+ledger allows replay of the previous ledger response while the original challenge remains current. A manual generation change rejects it, but no automatic independent durable generation fence/readiness gate/split-brain prevention exists. External key custody, valid bearer-proof theft, v2 canonicalization/constant-time MAC, PITR/HA remain unapproved/unproven. Revocation lock waits and general admission/DoS remain P1.
- Follow-up [S0-09C #19](https://github.com/alireza-anari/cac-project/issues/19) authorized for synthetic fail-closed recovery generation fencing and split-brain proof only, stacked on PR #18. Architecture gate [#9](https://github.com/alireza-anari/cac-project/issues/9) remains OPEN; historical [SOURCE-001 #1](https://github.com/alireza-anari/cac-project/issues/1) / `GATE-SOURCE` remain BLOCKED. No baseline acceptance, Production approval, product integration or Sprint 0 completion.


## S0-09C bounded evidence acceptance and deferred recovery gate — 2026-11-05

- Management reviewed [Draft stacked PR #20](https://github.com/alireza-anari/cac-project/pull/20) at exact final documentation head `8bd81906f6edbf1732e22c46ca8925c7dec1a595`, stacked on `work/s0-09b-issuer-pool-recovery-poc` at `75be54d0f18d6391014ca4e5d91466d62a6cf72c`. Executable implementation head `3a1138885a5c73e0b427a25b858fa399ff56cd24`; final two commits add docs only. **PR #20 stays Draft/unmerged; PRs #11/#16/#18 stay Draft/unmerged.**
- [Formal Architecture ruling](architecture/S0_09C_ARCHITECTURE_RULING.md): `S0-09C_EVIDENCE_ACCEPTED_WITH_LIMITS / RECOVERY_ARCHITECTURE_DEFERRED / NEW_IMPLEMENTATION_EXPERIMENTAL`. [Execution #19](https://github.com/alireza-anari/cac-project/issues/19) was CLOSED **strictly as the completed bounded synthetic evidence-handoff task**, NOT as an accepted recovery-fencing protocol, proof of physical disaster recovery or closure of wider security obligations.
- Final documentation-head synthetic PR CI: [C 42052172024](https://github.com/alireza-anari/cac-project/actions/runs/42052172024) SUCCESS (20 distinct S0-09C cases ×2, before/after local rollback/reapply, expected parent unsafe-restore RED), [full backend 42052172261](https://github.com/alireza-anari/cac-project/actions/runs/42052172261) SUCCESS (43 foundation +24 S0-09A +27 S0-09B cases, separately each ×2), and [focused B 42052172656](https://github.com/alireza-anari/cac-project/actions/runs/42052172656) SUCCESS. **114 distinct cases across separate workflows**, not a single combined 114-case suite. Final-head runs are synthetic PR merge-ref; exact executable-head Push evidence is separately linked in the handoff. No Management database rerun.
- [Handoff](https://github.com/alireza-anari/cac-project/blob/8bd81906f6edbf1732e22c46ca8925c7dec1a595/docs/S0_09C_HANDOFF.md) describes three separately initialized PostgreSQL 17.11 clusters on **one CI host**, a non-restored C anchor, monotonic CAS, committed-reader ACK, online checking, tested stale/restore denial, conservative OPEN, crash/rollback and ACL/fail-closed tests. It does not prove physical independent sites, PITR, quorum, network partitions or full signed/prod security.
- Independent read-only review found **3 Medium and 2 Low evidence/coverage findings**, no new bypass within stated trusted assumptions. Unmet P0: candidate-specific CAS/fence/OPEN RED mutations, C-fenced reused PgBouncer backend, external-anchor rollback/identity anti-rollback, and safe orphan OPEN reconciliation. An orphan OPEN may cause indefinite *safe* downtime; do not expire it without an approved proof.
- [S0-09D Issue #21](https://github.com/alireza-anari/cac-project/issues/21) tracks these missing security obligations as a separate experimental test task. `SOURCE-001 / GATE-SOURCE = BLOCKED`; [baseline acceptance #9](https://github.com/alireza-anari/cac-project/issues/9) remains **OPEN**; no approved trusted-context protocol, canonical baseline, Sprint 0 completion, product integration or Production release.


## S0-09D verdict: bounded evidence accepted; actual anchor rollback SECURITY FAIL — 2026-11-06

- [Final S0-09D Draft PR #22](https://github.com/alireza-anari/cac-project/pull/22) is stacked on C branch `work/s0-09c-recovery-fencing-poc` at `8bd81906f6edbf1732e22c46ca8925c7dec1a595`; final docs head `ca043e2751ea1dbcb7aed3c1ed3d171a9bb1f0e2`, executable head `8b490bfe5a64ac62c0a8382e77ce6a45486b4f04`. The final commit changes only four documentation files. PRs #11/#16/#18/#20/#22 remain **Draft, OPEN, UNMERGED**.
- [Official Architecture ruling](architecture/S0_09D_ARCHITECTURE_RULING.md): `S0-09D_EVIDENCE_ACCEPTED_WITH_LIMITS / ANCHOR_ROLLBACK_SECURITY_FAIL / RECOVERY_PROTOCOL_REJECTED_FOR_THIS_MODE / ARCHITECTURE_ACCEPTANCE_DEFERRED`. Execution [#21](https://github.com/alireza-anari/cac-project/issues/21) closed **only as a completed adversarial investigation/handoff**, **not** as satisfied security acceptance; P0 failures transferred explicitly to [S0-09E Architecture #23](https://github.com/alireza-anari/cac-project/issues/23) (DESIGN FIRST, OPEN).
- All six final-head CI runs are SUCCESS: [D Push 42105526148](https://github.com/alireza-anari/cac-project/actions/runs/42105526148), [D PR 42105536094](https://github.com/alireza-anari/cac-project/actions/runs/42105536094); [Full Push 42105526131](https://github.com/alireza-anari/cac-project/actions/runs/42105526131), [Full PR 42105535970](https://github.com/alireza-anari/cac-project/actions/runs/42105535970); [C PR 42105536034](https://github.com/alireza-anari/cac-project/actions/runs/42105536034) and [B focused PR 42105535941](https://github.com/alireza-anari/cac-project/actions/runs/42105535941). 129 distinct GREEN cases **across separate cohorts/workflows** (94 retained,20 C,3 mutation targets,4 pool,8 authority), with applicable roundtrip repeats; not a single 129-case suite. Candidate CAS/SQL Fence/OPEN negative mutation RED/RESTORED GREEN and actual C-fenced transaction-mode PgBouncer reused-backend denial were observed.
- **P0 OBSERVED FAILURE, EXCLUDED from GREEN count:** actual logical restore of C anchor's earlier schema from epoch2 to epoch1 **at unchanged PostgreSQL C system identity** revives prior owner A (`A.ready()=True`) who issues **fresh context** and reads scoped RLS; current B becomes unready. Both D logs record unchanged expected *security safety assertion RED* and exact restoration to current C state, followed by C20 GREEN. CI success proves detection of this unsafe scenario, **NOT safe anchor rollback**. The current C authority cannot be treated as a rollback-safe production root.
- Safe externally witnessed orphan OPEN reconciliation is not implemented: conservative deny-on-orphan causes potentially indefinite safe downtime; **no timeout clearing**. Physical PITR, same-identity physical clones, real asymmetric partitions, standby promotion, multihost HA, true wire-level lost COMMIT ACK and production custody/IdP/MFA/onboarding are NOT_RUN/unapproved.
- Next bounded action is **S0-09E design/ADR/security decision (#23)** on independently governed non-rollback monotonic authority, old signer hard-fencing/credential custody, and conservative orphan reconciliation before further PoC. [Baseline gate #9](https://github.com/alireza-anari/cac-project/issues/9) stays **OPEN**; [SOURCE-001 #1](https://github.com/alireza-anari/cac-project/issues/1) / `GATE-SOURCE` remain **BLOCKED**. No canonical baseline, product integration, Production deployment or Sprint0 completion.


## S0-09E Architecture design gate — 2026-11-06

- [Issue #23](https://github.com/alireza-anari/cac-project/issues/23) remains OPEN as the P0 **design-first** response to actual S0-09D Anchor rollback reviving former owner A; no security approval or automated recovery was granted.
- [Anti-Rollback Design Proposal](architecture/S0_09E_ANTI_ROLLBACK_DESIGN_PROPOSAL.md) recommends an independently governed, linearizable monotonic witness W and online guard verification as an **unproven candidate for independent read-only security review**; it compares rotated root/key identity and fail-closed manual pause alternatives.
- W itself must have independently verified anti-rollback custody, key and endpoint identity, freshness and failure domains. No stale/offline authorization; takeovers must exclude live old operations or prove hard fencing. Orphan OPEN remains blocked absent externally witnessed safe reconciliation. Physical clone/PITR, partition, lost COMMIT ACK and operational recovery remain NOT_RUN.
- Status `DESIGN_CANDIDATE_SELECTED_FOR_REVIEW / RECOVERY_PROTOCOL_PROPOSED / P0_SECURITY_GATE_BLOCKED`. PRs #11/#16/#18/#20/#22 remain Draft/unmerged; [Gate #9](https://github.com/alireza-anari/cac-project/issues/9) OPEN and [SOURCE-001 #1](https://github.com/alireza-anari/cac-project/issues/1) / GATE-SOURCE BLOCKED. No executable protocol change or Production approval.


## S0-09E independent review and R1 design refinement — 2026-11-06

- [S0-09E independent design review Draft PR #24](https://github.com/alireza-anari/cac-project/pull/24) at `dda6fea3347e582dfdcfc27299fbc8336b7233a0` is docs-only, unmerged; its [security review](https://github.com/alireza-anari/cac-project/blob/dda6fea3347e582dfdcfc27299fbc8336b7233a0/docs/security/S0_09E_DESIGN_READ_ONLY_REVIEW.md) identifies **4 P0 design-contract blockers**, 3 P1 refinements and 1 P2 bookkeeping finding. No W experiment or new CI ran; no exploit against a W implementation is claimed.
- Astra Management accepted the analytical findings via [formal review on PR #24](https://github.com/alireza-anari/cac-project/pull/24#pullrequestreview-5797117536) and registered [S0-09E targeted refinement R1](architecture/S0_09E_TARGETED_DESIGN_REFINEMENT_R1.md) on `main`. R1 addresses specification of W's *own* nonrollback trust root/restore continuity, restored verifier/clone admission, serialized durable OPEN holds through local COMMIT/ABORT and successor READY, and explicitly **excludes orphan OPEN clearing** from any initial PoC.
- `DESIGN_REFINEMENT_R1_PROPOSED / NOT_READY_FOR_IMPLEMENTATION_POC_AUTHORIZATION / P0_SECURITY_BLOCKED`. The root's actual continuity, clone exclusion and safe orphan outcome recovery remain unproved; no new W test has been executed. Existing S0-09D anchor rollback `FAIL_SECURITY` remains unchanged.
- [Architecture Issue #23](https://github.com/alireza-anari/cac-project/issues/23) remains OPEN for targeted **independent read-only R1 delta review**, before Management can consider any *strictly assumed-W, deny-only* integration PoC. Lane 2 real W-root/physical-restore proof and Lane 3 safe orphan clearing remain separately BLOCKED; no implicit implementation permission.
- PRs #11/#16/#18/#20/#22/#24 remain Draft/unmerged, Architecture [#9](https://github.com/alireza-anari/cac-project/issues/9) OPEN, SOURCE-001/GATE-SOURCE BLOCKED; `NEW_IMPLEMENTATION_EXPERIMENTAL / PROTOCOL_PROPOSED`. No Production, Sprint0, historical source-baseline, security-protocol or identity/onboarding approval.
