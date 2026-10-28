# S0-06 — Evidence-led SOURCE-001 recovery audit

**Outcome: no authentic v3.37/v3.38/v3.39 source recovered. SOURCE-001 / GATE-SOURCE remain BLOCKED.**

Astra Development / Work report for Astra Management, 2026-10-28 (Asia/Tehran). Approved architecture remains v3.37 / APR-036; APR-033/034/035 unchanged. This is a bounded inventory and provenance report, not a replacement baseline or an integration approval.

## Source reference and inspected scope

Repository: https://github.com/alireza-anari/cac-project. Starting main: `2f155cb70c1752837ae7dec53ac958ebf32fdfbb`. S0-05 was actually merged by Management before this audit. Work branch: `work/s0-06-source-provenance-audit`.

The five branch tips were obtained from GitHub and frozen in [refs.json](evidence/s0-06/refs.json). A non-shallow local fetch covered all their reachable commits, not only current filenames: **38 unique commits, 82 unique blobs, 61 distinct historical paths**. Every unique blob was read for `v3.37/v3.38/v3.39`, condensed variants, `APR-036` and `SOURCE-001`; 40 blobs contain textual references, not recovered baselines. Full history/path/blob results are in [audit.json](evidence/s0-06/audit.json).

| Actual branch | Tip | Classification |
|---|---|---|
| main | `2f155cb70c1752837ae7dec53ac958ebf32fdfbb` | Governance, corrected standalone v3.40, CI/contract tooling; no recovered backend |
| archive/v3.40-unpatched-reference | `0923d9bd761e04ba5bcf83c37e91ef7332f64c64` | Executable historical Python/SQLite module; not v3.37 |
| work/s0-source-recovery | `c2587da55f80d986bc8010ff8b398635bc0ae92c` | Exactly .gitignore, README.md, docs/PROJECT_STATUS.md; documentation only |
| work/sec-rev-001-standalone-import | `a0deaa53b0eb01e33820f9acd1b54b3d24d89e24` | Standalone security fix; imported through PR #3 |
| work/s0-05-ci-contract-hardening | `fa71168b4501e8bf3fc7da5205943d255f8842ae` | Tooling/summary-only API documentation changes; PR #6 |

GitHub REST inventory: **0 releases, 2 PRs (#3/#6), 7 issue-list entries (5 issues +2 PRs)**. Read all issue conversation comments, PR inline comments and reviews, including Management acceptance records. No archive URL or authentic older source ref was found. All collection pages requested `per_page=100&page=1` and had fewer than 100 entries. Exact requests/counts: [connected-searches.json](evidence/s0-06/connected-searches.json). The GitHub connector rejected the `/tags` endpoint (HTTP 400); **`git ls-remote --tags origin` succeeded with empty output**, independently confirming no advertised tags. This failure is not recorded as a successful API search.

History begins with repository initialization on 2026-10-27; fetched commits identify Alireza Anari as author. These are public repository attribution/date fields, not proof of original artifact authorship or an APR-036 signature. The historical module was imported via commits on October 27; no earlier v3.37/38/39 ancestry is present in the inspected refs.

## Actual accessible bytes and integrity

The current Project attachment at `project_sources/01-CAC-Project-Sources-v3.42.zip` was opened again. Read files 00–07 and VALIDATION_REPORT.json directly from ZIP; recursively inspected both embedded archives and checked their manifests. The report explicitly says original v3.37 and v3.38/v3.39 sources are unavailable; the member inventory independently contains none of those source archives.

Workspace inventory scanned the current workspace, excluding Git internals, dependency/venv directories and Python caches (exact exclusions in audit.json). **10 on-disk ZIP paths resolve to 6 distinct archive hashes**, including nested duplicates. All six archives pass ZIP CRC; **10 manifest files /257 listed entries match SHA-256**, including manifests embedded in prior Work evidence. No filename lead for v3.37/v3.38/v3.39 or named initial/RLS migrations was found outside excluded dependencies.

| Bytes actually inspected | Size | SHA-256 | Classification |
|---|---:|---|---|
| Project Sources v3.42 | 101556 | `c951e9656be6d35cf5b6a8b86129c5d80de5fd47c3bd0b7aeac446eba2271aa7` | Governance + nested references; 23-entry manifest |
| standalone v3.40 | 25597 | `e685e8872e953aff66daeeb6c551332f0dc6a178269f4041382c2f84c8e1118e` | Executable Python/SQLite reference; 16-entry manifest |
| handoff v3.41 | 41775 | `08316862c0afa60d500f7619dccaaee02ea92f60148111531e0f0aa6cee938bf` | Documentation + nested v3.40; 11-entry manifest |
| S0-01 evidence | 317680 | `f3ca10aacabd3a0e46276015dadf8b564855e839441124fbc937cc95f468d14f` | Prior audit artifacts; not original Freeze |
| S0-02 evidence | 86213 | `bdae7c4d6d146714bc0ef4a3e2d0280944c1ecf85560a491050fa427315ac39f` | Corrected standalone module and evidence |
| S0-03 handoff | 111923 | `94f4d586023779500ea85a8cc7f76f092817e6b7da8a0dcb06aec2e59391a240` | Handoff/evidence, including S0-02; not backend |

Full relative paths, nested member inventory, manifest digests and match counts are recorded in audit.json. Hash matches prove byte consistency with the supplied records; **they do not prove architectural authenticity, ownership rights or approval under APR-036**. No expected v3.37/38/39 hash is available, and none has been invented.

## Connected search and inaccessible leads

Fresh, metadata-only Google Drive queries: `v3.37`, `v3.38`, `v3.39`, `APR-036`, `cac-v3.39-implementation-sprint-02.zip`, `CAC`, `v337`, `v338`, `v339`, `Architecture Freeze`. Nine yielded no results. `CAC` yielded three unrelated cache-named folders; none were opened and their private IDs/names/URLs are excluded from public evidence. No next-page token was returned. This bounded keyword search is not a complete Drive export or proof of global absence.

Conversation context mentions a prior file named `cac-v3.39-implementation-sprint-02.zip` and migration filenames `0001_initial.py` / `0002_postgresql_rls.py`. Those are **leads only**: no bytes are attached/selected for those files in this conversation, and no matching current workspace or Drive candidate was found. Other-conversation Library attachments are not accessible under this session's permissions and were not searched/read. No claim is made to have examined their contents, provenance, or hashes. Management must attach the actual files or provide a permitted exact source location.

Not inspected: deleted/unadvertised remote refs, unreachable objects not supplied by GitHub, other repositories not identified by a grounded source link, other devices/backups, inaccessible Drive accounts, Library files from other conversations, private conversations or original approval evidence not supplied here. No broader account/source access is inferred from keyword results.

## Actual diff and compatibility boundaries

Seven source/test/API files in the historical v3.40 branch were re-read and compared with the original nested ZIP: **7/7 byte-identical**. Current standalone differs in `service.py` (SEC-REV-001), three OpenAPI summaries, and added `tests/test_revocation.py`. Exact hashes: [existing-source-comparison.json](evidence/s0-06/existing-source-comparison.json). Exact source/API/test patch: [v340-to-current-standalone.patch](evidence/s0-06/v340-to-current-standalone.patch). The patch deliberately excludes unrelated packaging/docs; it is not presented as a whole-repository diff.

`storage.py`, `policy.py`, original tests and adapter-port definitions are unchanged. This establishes continuity of the known standalone reference only. It does not establish compatibility with missing Django models, a PostgreSQL migration graph, RLS policies or the frozen OpenAPI. **v3.37→v3.38→v3.39 diff and migration/API compatibility: BLOCKED, not computable without bytes.** No Django scaffold, migration, policy or API substitute was generated or run. No new application tests were run for this documentation-only audit; prior 45/9 results remain historical S0-05 evidence, not S0-06 runs.

## Public-safety and provenance assessment

No new source candidate was found; there is no recovered archive eligible for publication. **No archive is added to GitHub.** Publication is limited to this report, reproducibility script, bounded metadata, checksum results and a diff of source already public in this repository. The original evidence ZIPs and private Drive identifiers are withheld.

Reviewed public payload for credential/key patterns, customer identifiers, personal data and unnecessary private source details. The patch contains already-public synthetic fixtures; metadata contains public Git attribution and authorized CAC artifact names/hashes, not credentials/customer records. Heuristic scans and manual inspection are limited reviews, not malware/vulnerability certification. Original archive publication rights and architectural authenticity are not inferred from ownership of the public repository; future recovered archives need separate content, rights and provenance review before upload.

## Executed commands / reproducibility

Run from repository root; Python standard library only. Current execution used Python 3.12.14 on Linux. Git fetch and inventory are read-only to the remote.

```bash
git fetch origin --prune --tags
git ls-remote --tags origin
git rev-parse --is-shallow-repository
git log --all --format='%H %aI %an %s'
git ls-tree -r --name-only origin/work/s0-source-recovery
python tools/source-audit/audit.py \
  --workspace /workspace/scratch/9851e9d0909c \
  --refs docs/evidence/s0-06/refs.json \
  --output docs/evidence/s0-06/audit.json
python tools/source-audit/compare.py \
  --project-zip /workspace/scratch/9851e9d0909c/project_sources/01-CAC-Project-Sources-v3.42.zip \
  --refs docs/evidence/s0-06/refs.json --output-dir docs/evidence/s0-06
```

The audit script enumerates snapshots with `git rev-list` / `git ls-tree -rz`, reads every unique blob with `git cat-file`, reads ZIP bytes without extraction/execution, checks CRC, verifies each SHA-256 manifest entry and deduplicates nested ZIPs by hash. It exits nonzero on manifest failure or safety-limit violation. Actual audit exit **0**, 38 commits/82 blobs/61 paths/6 unique ZIPs, zero manifest failures; see [audit-run.log](evidence/s0-06/audit-run.log). Git tag listing exit **0**, zero lines. Comparison script exit **0**; see [compare-run.log](evidence/s0-06/compare-run.log). Script output is a measured snapshot, not a source-authenticity assertion. A rerun needs the same archive bytes and reachable commits; connected searches are time/account dependent and cannot be replayed by the offline script.

## Gate decisions / exact unblock request

| Gate | Decision | Evidence / dependency |
|---|---|---|
| Accessible archive integrity | PASS | CRC +257 manifest-entry comparisons |
| Historical v3.40 identity | PASS, scoped | Seven exact blob matches |
| Approved source recovery | **BLOCKED** | No v3.37/38/39 bytes or authentic refs |
| Freeze compatibility, migration graph, backend bootstrap | **BLOCKED / NOT_RUN** | Missing source and approval linkage |
| PostgreSQL/RLS, concurrency, Django/production | **NOT_RUN / BLOCKED** | No valid baseline; no deployment performed |

**Management action (P0, owner: Astra Management with original artifact custodian):** provide the original v3.37 ZIP and v3.38/v3.39 ZIPs as actual attachments, or exact repository URL + reachable commit/tag and read access. Include the original delivery date/creator, available original checksums/manifests and the approval record linking the exact version/artifact to APR-036. For the v3.39 conversation lead, reattach the named ZIP and its validation report; filenames alone do not unblock SOURCE-001. If the files live elsewhere, provide the exact permitted file link/account rather than a generic product/version name. Private artifacts should be supplied through an authorized private channel before any public publication decision.

Then Work can verify bytes/provenance, review secrets/publication rights, compute version diffs and the real migration graph, and request Architecture compatibility review. Until then Issue #1 remains open/BLOCKED, Sprint 0 remains incomplete, and APR-036 is not replaced by the available standalone code.
