# CAC — Source registry (historical and current)

> This is a declaration of evidence availability, not a source-integrity certificate for files not yet committed. Values below originate from the Project Sources v3.42 reference package and separate reported S0-03 delivery.

| Artifact | SHA-256 | Role / integration status |
|---|---|---|
| CAC Project Sources v3.42 ZIP | `c951e9656be6d35cf5b6a8b86129c5d80de5fd47c3bd0b7aeac446eba2271aa7` | Documentation/handoff bundle; exists in project context |
| v3.40 standalone onboarding ZIP | `e685e8872e953aff66daeeb6c551332f0dc6a178269f4041382c2f84c8e1118e` | Original independent Python/SQLite module; **not** integrated |
| v3.41 Work Handoff ZIP | `08316862c0afa60d500f7619dccaaee02ea92f60148111531e0f0aa6cee938bf` | Handoff documentation |
| SEC-REV-001 standalone corrected ZIP | `bdae7c4d6d146714bc0ef4a3e2d0280944c1ecf85560a491050fa427315ac39f` | S0-02 artifact **reported**; not directly available in the current Project ZIP |
| S0-03 handoff ZIP | `94f4d586023779500ea85a8cc7f76f092817e6b7da8a0dcb06aec2e59391a240` | S0-03 **reported**; source bytes and security review pending direct access |
| v3.37 Architecture Freeze source | — | MISSING / SOURCE-001 BLOCKED |
| v3.38 Django Scaffold source | — | MISSING / SOURCE-001 BLOCKED |
| v3.39 PostgreSQL RLS source | — | MISSING / SOURCE-001 BLOCKED |

Important: The SHA-256 values for S0-02 and S0-03 are **reported from the Work handoff** and are not independently reverified by this GitHub repository.

## Correct provenance workflow

1. Obtain the authentic archive/reference.
2. Verify hash and internal manifest; record actual file set, provenance and publication scan.
3. Commit exact imported content to a branch, annotate whether historical/unpatched or corrected.
4. Connect build/test artifacts to a commit SHA and run clean-environment tests.
5. Keep `SOURCE-001` blocked until actual v3.37 source/reference is verified.

## Security remediation

A flaw in original standalone v3.40 `revoke_capability` was reported: a pending invitation could survive revoke if no active grant existed. A later standalone fix is reported with **13 added + 32 original passing tests**, but remains **NOT_MERGED / SOURCE_UNVERIFIED**, and PostgreSQL accept/revoke race tests were designed but NOT EXECUTED.

Do not describe the original v3.40 source as the corrected security release.
