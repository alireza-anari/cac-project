# CR-S0-05-001 — invitation error response contract

**Status: PROPOSED / NOT APPROVED / NOT IMPLEMENTED.** Requester: Astra Development; approval owner: CAC Architecture, coordinated by Astra Management. This document does not change APR-036 or authorize integration.

## Reason and baseline

Redocly 2.71.2 `operation-4xx-response` reports that `POST /api/v1/admin/stores/{store_id}/invitations` has only a 202 response. Baseline is the standalone addendum at main `2e62137defc2d53819fc0ba8bf42283dfeb7bbeb`; its exact original SHA-256 is in `docs/evidence/s0-05/execution.json`. The frozen v3.37 contract is unavailable (SOURCE-001).

## Current / desired behavior

Current design documents owner/delegability/fresh-MFA constraints but no failure response for this operation. Proposed contract: explicitly describe a generic 403 for authorization failure, without leaking target membership/existence or issuing an invitation. Exact mapping of unauthenticated, malformed, CSRF, rate-limited and conflict failures must be compared to the recovered baseline before approval; no status is inferred from SQLite exceptions.

Candidate API diff (proposal only; not applied to OpenAPI):

```diff
 responses:
   '202': ...
+  '403':
+    description: Request not authorized; no invitation issued (safe disclosure)
```

## Impact

- API: adds a documented response; error-body schema remains a decision for Architecture after baseline recovery. No change implemented.
- DB/schema: none proposed. Product: successful invitation behavior unchanged. UX: clients can handle a documented denial.
- Security: uniform denial must not disclose cross-store/target identity; deny before writes/delivery, preserve MFA and audit policy.
- Compatibility: existing successful requests unchanged; compatibility of real status/body mapping is unknown until baseline retrieval. Do not generate integrated clients from this proposal.

## Acceptance/test plan

After approval and verified backend: cover nonmember, wrong store/tenant, nondelegable capability, stale MFA and CSRF failure; prove generic approved errors, no grant/invitation/delivery side effects, appropriate audit, and unchanged authorized 202. Rerun contract lint and real integration tests. SQLite and current lint do not validate these future HTTP behaviors.

## Work action

Keep the warning visible in CI; do not invent responses to obtain zero warnings. Escalate proposal to CAC Architecture through this reviewable PR. Integration depends on SOURCE-001 and separate authorization.
