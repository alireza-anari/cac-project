# CAC — Public Project Status

_Last updated: 2026-10-27. This is a management status record, not independent CI evidence._

## Authorized architecture

The approved architectural baseline is **v3.37 / APR-036**. Preserved decisions include **APR-033**, **APR-034**, and **APR-035**. Architectural contract changes require a reviewed change request (CR).

## Source registry

| Source | Status |
| --- | --- |
| v3.37 approved baseline | Original source archive not recovered; **SOURCE-001 BLOCKED** |
| v3.38 / v3.39 | Original sources not recovered |
| v3.40 standalone onboarding | Referenced locally, **not integrated** |
| S0-02 security remediation | Verified artifact; corrected standalone source imported on Work branch; **NOT_MERGED / SOURCE_UNVERIFIED** |
| S0-03 evidence handoff | Actual archive/hash/manifest verified; Management acceptance pending |
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

## S0-04 Work branch

Corrected artifact bytes and original reference branch were verified. Source lives under `standalone/onboarding/`; installation metadata and standalone-only GitHub Actions are added. See [handoff](S0_04_HANDOFF.md). No backend integration, migration, deployment or merge is claimed. SOURCE-001 and all integrated gates remain BLOCKED.
