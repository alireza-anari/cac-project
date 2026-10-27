# Original CAC v3.40 standalone onboarding — HISTORICAL / UNPATCHED

This branch records the **original standalone v3.40** source as a historical reference, **not** the S0-02 security-fixed release.

The original version contains the documented `SEC-REV-001` invitation-revocation flaw: `revoke_capability` previously skipped invalidating pending invitations if no grant was active. **Do not deploy or reuse as a secure service.**

Original source archive SHA-256: `e685e8872e953aff66daeeb6c551332f0dc6a178269f4041382c2f84c8e1118e`.

- Architecture approval: `v3.37 / APR-036` (actual main source not recovered).
- SQLite reference implementation only; Django/PostgreSQL/RLS/MFA integration not established.
- Reported old tests: 32 original unit tests. This Git branch import is NOT evidence of their execution.
- The corrected standalone S0-02 artifact has a different reported SHA and is **not imported here**.

State: `NOT_MERGED / SOURCE_UNVERIFIED`. Do not merge this branch into `main`.
