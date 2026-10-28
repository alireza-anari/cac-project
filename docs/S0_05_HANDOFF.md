# S0-05 — standalone CI hardening and contract validation

**Work handoff for Astra Management. NOT_INTEGRATED / SOURCE_UNVERIFIED.**
Base: main `2e62137defc2d53819fc0ba8bf42283dfeb7bbeb`, after confirmed PR #3 merge `a6f7818bb4b2bfa0db24d5007dcc924bfaeaf8ed`.
Branch: `work/s0-05-ci-contract-hardening`. No auto-merge. The final head and actual CI run are recorded in [PR #6](https://github.com/alireza-anari/cac-project/pull/6); local results are not CI results.

## Changes and reproducibility

- Runtime service, policy, storage and all 45 tests unchanged. No API semantic or DB/schema change. Migration: none created/executed. OpenAPI gains three operation summaries only; parsed documents compare equal after removing those three additions. Exact before/after hashes: [execution.json](evidence/s0-05/execution.json). Historical provenance remains intact.
- Actions are pinned to verified upstream release commit SHAs, not floating tags. Release metadata and `action.yml`/README reviewed for Node 24 and runner requirements (minimum v2.327.1; GitHub-hosted Ubuntu 24.04). No claim of full source/security audit of bundled Action JavaScript.
- Python CI 3.12.15; Node 24.22.1 with an explicit npm 11.19.1 version assertion; Redocly 2.71.2 with npm tarball integrity; pip 26.2.2 and setuptools 84.2.1 with PyPI wheel SHA-256. Build installs with `--require-hashes --only-binary=:all:`, then `--no-build-isolation --no-deps`. Runtime dependencies remain empty.
- `npm ci --ignore-scripts --no-audit --no-fund` consumes committed lock; no floating npx download. No caching. Package registries, hosted OS images, runner and bootstrap pip remain external dependencies; this is not a hermetic/bit-identical build or vulnerability attestation. Redocly bundles dependencies, so the single npm lock entry is a distribution integrity guarantee only.

| Action | Reviewed release | Commit SHA |
|---|---|---|
| actions/checkout | v7.0.1 | 3d3c42e5aac5ba805825da76410c181273ba90b1 |
| actions/setup-python | v7.1.0 | 6d4fd22b20465ccc0f7354476588e8df7c9ca0e0 |
| actions/setup-node | v7.1.0 | 949feb2413d6458794dcd2491c4babbbce0c15c1 |
| actions/upload-artifact | v7.0.2 | cf430e030ddbb5b0abf93d22962f4752f3646cd9 |

Upstream records: [checkout](https://github.com/actions/checkout/releases/tag/v7.0.1), [setup-python](https://github.com/actions/setup-python/releases/tag/v7.1.0), [setup-node](https://github.com/actions/setup-node/releases/tag/v7.1.0), [upload-artifact](https://github.com/actions/upload-artifact/releases/tag/v7.0.2). Redocly: [lint docs](https://redocly.com/docs/cli/commands/lint) and [release source](https://github.com/Redocly/redocly-cli).

## Commands and local evidence

See [package README](../standalone/onboarding/README.md) for clean Python installation and [validator README](../tools/contract-validation/README.md) for lock installation and lint. From `standalone/onboarding` with the clean venv active:

```bash
PYTHONPATH=. python -m unittest discover -s tests -p 'test_*.py' -v
```

From repository root:

```bash
REDOCLY_TELEMETRY=off npm --prefix tools/contract-validation run validate
REDOCLY_TELEMETRY=off npm --prefix tools/contract-validation run lint
REDOCLY_TELEMETRY=off npm --prefix tools/contract-validation test
```

| Local verification | Result / exit | Evidence |
|---|---|---|
| Clean Python build tools, install, out-of-tree import | PASS / 0 | [install summary](evidence/s0-05/install-summary.log) |
| Original + revocation tests | 45 PASS, 0 FAIL/errors/skips / 0 | [full log](evidence/s0-05/unittest.log) |
| Original structural profile | PASS / 0 | [before](evidence/s0-05/structure-before.log) |
| Original recommended lint | FAIL: 4 errors, 2 warnings / 1 | [before](evidence/s0-05/lint-before.log) |
| Final independent spec profile | PASS / 0 | [after](evidence/s0-05/structure-after.log) |
| Final scoped recommended lint | PASS: 0 errors, 1 known warning / 0 | [after](evidence/s0-05/lint-after.log) |
| Real CLI gate fixtures | 9 PASS, 0 failures/skips / 0 | [fixture log](evidence/s0-05/lint-gates.log) |

Local Linux: Python 3.12.14, SQLite 3.53.1; CI Python is pinned separately. Environment and hashes are in execution.json. Initial local npm was 11.9.0; the first real CI exposed bundled npm 11.19.1, so final lock installation and contract checks were repeated locally with 11.19.1 and CI now rejects version drift. npm's local proxy-config/dependency-update notices are preserved in logs; they are not contract warnings. No proxy URLs or environment dump is published. Installation summary intentionally excludes index configuration and local temporary paths.

## Contract findings, decisions and CR

Three `operation-summary` errors were corrected with summaries. `no-empty-servers` is disabled only in the recommended profile because no deployment URL is authorized. `info-license` is disabled only there because public visibility is not a license grant. The structural profile is separate and has no policy exceptions. No ignore file or blanket forced-success is used.

The remaining `operation-4xx-response` warning applies to invitation creation. It stays visible at warning severity. [CR-S0-05-001](changes/CR-S0-05-001-invitation-error-response.md) proposes a safe denial response for Architecture review; the OpenAPI response contract is not changed. Scoped lint success is not zero-warning or complete API-design acceptance.

Nine fixtures exercise both profiles with valid 3.1.1 nullable schemas, invalid schema types, unresolved local references, duplicate operation IDs, plus missing summary rejection under recommended lint. Nonzero CLI status and diagnostic rule IDs are asserted, so absence of the executable cannot produce a false positive.

## CI and security boundaries

Workflow permissions remain `contents: read`; checkout uses `persist-credentials: false`. No `pull_request_target`, secret env inputs, credential persistence, cache or AI/provider operations. Each evidence upload lists individual files, excludes hidden files, and never captures `.git`, npm config, home, environment dumps, dependency trees or arbitrary evidence-directory contents. Logs contain synthetic test fixtures. This reduces accidental collection; it is not a guarantee against malicious changes to executed PR code. Only public hosted runners and read-only context are used.

Tests and contract validation are separate jobs, each fail-closed and bounded to 10 minutes. Discovery must find at least 45 Python tests. Tool, module and workflow path changes trigger checks. Upload runs even on failure, retaining logs and exit codes for 30 days. Tests, structural lint, scoped lint and fixture exit codes are not swallowed. CI records actual checkout and PR-head SHA separately; PR synthetic merge is not a real merge.

## Gate decisions and residual risks

- Standalone local install/tests and scoped contract checks: PASS, with the one declared warning/CR.
- CI: final outcome must be attached to the real head in PR checks, not inferred here.
- SOURCE-001 / GATE-SOURCE / BOOT / MIG / TENANT / ONBOARD: BLOCKED. No historical baseline recovered.
- PostgreSQL/RLS/race testing, Django, live IdP/MFA/CSRF, append-only production audit: NOT_RUN / BLOCKED.
- APR-033/034/035/036 unchanged. No production release or AI connection performed. Neither Sprint 0 nor Sprint 1 is completed by this change.

## Next actions

1. P1 Management: review separate PR, exact head, CI job logs and explicit lint exceptions; do not auto-merge.
2. P1 Architecture: decide CR-S0-05-001 after mapping the recovered baseline; retain the visible warning meanwhile.
3. P0 Management: supply authentic v3.37/v3.38/v3.39 bytes or repository refs to unblock SOURCE-001.
4. P0 Work/DB after source recovery: execute real adapter/migration/RLS and PostgreSQL accept/revoke race checks.
5. P1 Work: periodically review pinned Action/tool updates and rerun negative fixtures; pins prevent drift but require maintenance.

## Independent S0-05 review

Read-only reviewer inspected the full tracked diff and new files, independently reran 45 Python tests, nine real CLI fixtures, structural validation and `git diff --check`: PASS. No Critical/Important/Minor findings. Review did not revalidate upstream release SHA metadata, audit bundled dependencies, execute GitHub Actions or assess absent backend/production. Local review needed a writable scratch TMPDIR because its sandbox lacked `/tmp`; the rerun passed. This review supports opening the PR, not merge or production approval.
