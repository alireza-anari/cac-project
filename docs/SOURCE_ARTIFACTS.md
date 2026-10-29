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

## S0-07 experimental new-origin foundation — 2026-10-29

Source ID **CAC-NEW-ORIGIN-S0-07 / NEW_IMPLEMENTATION_EXPERIMENTAL**; implementation commit `741ee42471fea8c7a7a8780305eddcaeb9f72d31`, based on main `025931e0a612ff95c8165dec7c82af0d922b181a`. New Django/PostgreSQL code under `experimental/backend/`; no historical source archive imported or reconstructed. Draft [PR #11](https://github.com/alireza-anari/cac-project/pull/11) and [Work evidence/limitations](S0_07_HANDOFF.md). Real PostgreSQL foundation tests do not establish historical provenance or product integration. **SOURCE-001 and GATE-SOURCE remain BLOCKED**; Architecture #9 approval and security review are required before promotion.
