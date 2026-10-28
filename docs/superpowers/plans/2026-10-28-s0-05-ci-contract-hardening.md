# S0-05 CI and contract hardening implementation plan

> Execute inline with superpowers:executing-plans; final independent review.

**Goal:** Reproducible standalone tests and OpenAPI 3.1.1 structural/lint gates.
**Spec:** Astra Management S0-05 mission in this conversation.
**Architecture:** Keep Python runtime and API semantics unchanged. Pin supported Actions to verified release commits; lock development tooling. Use Redocly structural and recommended lint profiles, documenting exceptions required by the unintegrated design addendum.
**Constraints:** APR-036 unchanged; SOURCE-001 BLOCKED; no migration, backend integration, deployment, AI call or auto-merge.
**Approach decision:** Redocly provides 3.1-aware spec validation and style checks in one pinned tool. Avoid a second overlapping validator and avoid inventing servers/licenses/response contracts to silence lint.

## Task 1 — contract tooling
- [x] Install exact Redocly version with npm lock integrity and scripts disabled.
- [x] Run spec/recommended checks on original file; record actual findings.
- [x] Apply documentation-only corrections, or record justified rule exceptions/CR for semantic proposals.
- [x] Exercise invalid structures, unresolved references, duplicate operation IDs and valid nullable 3.1 schemas; prove gates fail/accept appropriately.

## Task 2 — workflow reliability
- [x] Verify release tags, commit SHAs and action.yml runtime requirements.
- [x] Pin Python/Node versions; upgrade pinned build tooling; preserve installed-package check and all 45 tests.
- [x] Add separate contract job and trigger coverage; permissions contents:read, credentials false, no caches/secret env dumps, explicit evidence allowlist.
- [x] Run clean local install, tests, lint and tooling checks; inspect logs and diff.

## Task 3 — handoff
- [x] Update README and evidence report; preserve historical provenance.
- [x] Independent whole-change review; resolve material findings.
- [ ] Publish separate branch/PR; inspect real CI at exact head and record results. Do not merge.

## Review focus
Bad 3.1 schemas and unresolved refs must fail; lint exceptions must not hide structural faults; zero discovered tests must not pass; tool/workflow edits must trigger CI; artifact paths must not capture environment dumps or credentials.

## Decisions / execution ledger
- Management explicitly delegated normal technical choices: no extra design-approval pause.
- Base main 2e62137defc2d53819fc0ba8bf42283dfeb7bbeb; PR #3 actually merged.
- Branch is isolated from main; existing clean checkout reused.

- Task 1/2 local verification complete: 45 service tests and nine CLI fixtures pass; scoped lint has one visible 4xx warning.
- Ruling: separate spec.yaml avoids automatic recommended-config discovery; both profiles tested explicitly.
- Ruling: missing server/license are documented profile exceptions, not invented contract values. Missing 4xx response remains visible with CR.
- Independent final reviewer: 0 Critical/Important/Minor; independently reran 45 Python tests, nine CLI fixtures and structural validation. Ready for PR/CI, not merge.

- CI evidence exposed npm version difference (local 11.9.0 vs Node CI bundled 11.19.1): pin by explicit CI assertion, correct docs, rerun local npm ci and contract checks with 11.19.1, then recheck final-head CI. Initial CI passed but is superseded.
- Final local npm 11.19.1 clean ci, structural and scoped lint checks and nine CLI fixtures: exit 0; version guard rejects 11.9.0 (exit 1).
