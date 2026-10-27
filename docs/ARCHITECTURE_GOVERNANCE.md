# CAC — Architecture & authority

Reference documents package: **CAC Project Sources v3.42** (governance and handoff, not product source or a new Freeze).

Approved architecture **v3.37 / APR-036** remains the only frozen baseline.

| Decision | Constraint |
|---|---|
| APR-033 | Verified qualifying contact is required before public Live |
| APR-034 | At most one public active assistant per store in V1 |
| APR-035 | Confirmed loss of final qualifying contact pauses public access while preserving private Preview; transient probe failure alone does not trigger pause |
| APR-036 | Architecture v3.37 is frozen |
| CR-340-001 | Standalone onboarding design; not proven integrated into the application |

**Roles:** CAC Architecture approves architecture/contract changes through CR; Astra Management prioritizes, tracks gates and reviews delivery; Astra Development / Work produces actual code, migrations, tests, commit references and artifacts.

Any proposed change to API, schema, security boundary, assistant Live constraints, Woo private-data scope, retention or product requirements needs impact analysis and a CR. Documentation and developer fixes do not silently supersede the approved Freeze.

This repository being created does **not** retroactively establish that v3.37/v3.38/v3.39 source was recovered.
