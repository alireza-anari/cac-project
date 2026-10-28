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

A separate branch hardens Action/dependency pins and adds OpenAPI 3.1.1 structural/lint checks and negative fixtures. See [S0-05 handoff](S0_05_HANDOFF.md) for actual local results and known warning/CR; CI acceptance comes from the PR head checks. Runtime behavior and API semantics are unchanged. SOURCE-001 and all integrated gates remain BLOCKED. This entry does not predeclare Management acceptance or merge.
