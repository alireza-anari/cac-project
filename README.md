# CAC Project

Official development repository for CAC.

> **Current state:** `SOURCE_UNVERIFIED` / `NOT_MERGED`. A public repository and documentation bootstrap have been created; the authentic v3.37 baseline and later v3.38/v3.39 sources have not yet been recovered, and Django/PostgreSQL integration is not verified.

## Documentation

- [Execution Roadmap](docs/MVP_ROADMAP.md) — Sprint 0–6 scope and exit gates
- [Architecture Governance](docs/ARCHITECTURE_GOVERNANCE.md) — APR-033/034/035/036 and change control
- [Source Registry](docs/SOURCE_ARTIFACTS.md) — known references, checksums and outstanding artifacts
- [Security Release Gates](docs/SECURITY_RELEASE_GATES.md) — expected tests and evidence
- [Current Project Status](docs/PROJECT_STATUS.md) — delivery and integration status

## Development process

1. Work performs source/code imports and actual development on a feature branch.
2. Commit source and test evidence with real SHA references and no unsupported PASS claims.
3. Astra Management reviews the evidence and decides if an acceptance gate is satisfied.
4. Architecture contract changes require a documented CR and approval.
5. Integrate only after the authentic baseline and relevant migration/security gates are verified.

## Publication policy

This repository is intentionally **public at the owner's direction**. Reviewed source code, project documents, tests and appropriate evidence may be published with clear provenance and integration labels. Never commit **real passwords, secret keys, access tokens, credentials or private customer data**, regardless of visibility.

Historical standalone v3.40 contained a reported revoke/invitation security defect. It is not the corrected S0-02 security fix, and should not be used as a production onboarding service.

No product release or production deployment is authorized by this repository bootstrap.

## Standalone security remediation

The reviewed standalone SEC-REV-001 source was imported into [standalone/onboarding](standalone/onboarding/README.md) on `main` via [PR #3](https://github.com/alireza-anari/cac-project/pull/3), merged in commit `a6f7818bb4b2bfa0db24d5007dcc924bfaeaf8ed`. See [S0-04 handoff](docs/S0_04_HANDOFF.md) for provenance, local test evidence and integration blockers. Import into this repository does not recover the frozen backend or establish application integration.
