# CR-S0-09D-001 — Proposed authority recovery boundary

Status: **PROPOSED / protocol acceptance DEFERRED**. 2026-11-06 (Asia/Tehran). References: [Issue21](https://github.com/alireza-anari/cac-project/issues/21), [Draft PR22](https://github.com/alireza-anari/cac-project/pull/22), [handoff](../S0_09D_HANDOFF.md), [independent review](../security/S0_09D_FINAL_READ_ONLY_REVIEW.md). Executable evidence pinned to8b490bfe5a64ac62c0a8382e77ce6a45486b4f04.

## Observed decision input

Independent candidate CAS/SQL/OPEN sensitivity and bounded real PgBouncer composition passed. An authenticated authority clone with a different system identifier is rejected. But restoring C's old logical schema at the same C identity revives previous-owner issuance/RLS after takeover. Its original denial assertion remains SECURITY RED. Safe orphan clearing is absent and intentionally BLOCKED. These results justify accepting the experiment record, not the recovery/security protocol.

## Authority alternatives to evaluate separately

| Candidate boundary | Benefit | Unresolved obligation |
|---|---|---|
| Current single C identity plus restored C state | Simple synthetic coordinator; tested fail-closed on supported outages | Observed epoch rollback revives authority. Reject this as a safe rollback recovery mode; WAL settings and SID pinning do not establish anti-rollback |
| Separately governed non-rollback high-watermark/witness | Could detect a restored authority below the last accepted generation | Define independent trust/failure domain, custody, atomicity, availability and fencing guarantees; then test witness outage, rollback/clone and races. No implementation approved here |
| New authority identity/key epoch after restore plus independently verified hard fencing | Could make old authority/material unusable after recovery | Prove all old primaries/anchors are fenced and key/identity rotation is non-rollbacked. Defining such a custody/recovery contract is separate architecture work, not an assumption that changing one UUID is sufficient |

Same-identity physical clone behavior is currently an inference from shared identity/material, NOT_RUN as an actual physical experiment. A differently initialized clone's rejection does not establish that mode's safety. No quorum/HA/KMS product or production custody system is selected by this CR.

## Proposed orphan recovery requirements

Do not clear OPEN, reset ownership or revive an old lease merely because a timer expires, a backend disappeared or local logs look quiet. Before any clearing implementation, a separately reviewed protocol must establish independent fencing of the prior authorized actor, trustworthy local transaction outcome or a defined conservative resolution, monotonic generation revocation outside a rollbackable snapshot, and a durable auditable reconciliation receipt. Test ambiguous/lost outcomes, restart/restore, clone, concurrent reconciliation and witness outage. These are proof requirements, not a claim they are sufficient or implemented.

Until then, preserve indefinite fail-closed downtime. Fixture reset/restore used to run experiments is never an operational reconciliation procedure.

## Proposed architecture disposition

1. Record bounded Phase1 sensitivity and Phase2 pool results as accepted evidence; preserve all94 inherited and20 C tests.
2. Reject the demonstrated anchor-rollback mode for authorization recovery; keep its safety assertion RED until a real reviewed control makes it GREEN. CI may validate an expected unsafe observation without granting protocol acceptance.
3. Require a separate Architecture ruling for anti-rollback identity/custody and safe externally witnessed orphan recovery. Include the NOT_RUN matrix in any later acceptance claim.
4. Retain NEW_IMPLEMENTATION_EXPERIMENTAL / PROTOCOL_PROPOSED, SOURCE-001/GATE-SOURCE BLOCKED and Gate9 OPEN. Keep all stacked PRs Draft/unmerged. No APR-033/034/035/036 change, production/IdP/MFA/onboarding integration, v2/TTL/key-management approval, historical-source claim or Sprint0 completion.
