# Standalone OpenAPI validation

Run from repository root with Node **24.22.1** (bundled npm **11.9.0**):

```bash
npm ci --prefix tools/contract-validation --ignore-scripts --no-audit --no-fund
REDOCLY_TELEMETRY=off npm --prefix tools/contract-validation run validate
REDOCLY_TELEMETRY=off npm --prefix tools/contract-validation run lint
REDOCLY_TELEMETRY=off npm --prefix tools/contract-validation test
```

Redocly CLI **2.71.2** is exact-pinned; npm lockfile stores the registry tarball SHA-512 integrity. This release bundles its dependencies into the CLI distribution (one lock entry); integrity is not an audit of bundled dependency vulnerabilities. No remote API/provider login, push or AI command is used. Lifecycle scripts and telemetry are disabled; installation still needs public npm access. Runtime backend has no new dependency.

`validate` uses Redocly's OpenAPI `spec` rules; `lint` uses `recommended` with explicit exceptions in `redocly.yaml`. Both accept OpenAPI **3.1.1** and JSON Schema nullable type arrays. Nine real CLI tests prove acceptance of a valid fixture and rejection of invalid types, missing refs, duplicate operation IDs and missing summaries. Fixtures are synthetic, in temporary directories, deleted after use.

## Explicit scope, not a zero-warning claim

The addendum is undeployed: `no-empty-servers` is off rather than fabricating a URL. `info-license` is off because the owner has not granted a license. These are documentation-policy exceptions, not suppressed structural validation. `operation-4xx-response` remains **warn**: issue-invitation has no 4xx contract. See [CR-S0-05-001](../../docs/changes/CR-S0-05-001-invitation-error-response.md). Three missing summaries were added without changing paths, request/response schemas, security or operation IDs.

No ignore file, force-success flag, remote dereferencing fixture or baseline reconstruction is used. A successful scoped lint currently means **0 errors, 1 known warning**, not complete API design or Freeze compatibility.

## Maintenance

Review release notes, version engine requirements, lock integrity and negative fixtures before updates. Regenerate the npm lock deliberately and run `npm ci`, both profiles and tests; do not use floating `npx latest` in CI. Hosted OS images and package registries remain external mutable availability dependencies; this is repeatable tool selection, not a hermetic or bit-identical build.
