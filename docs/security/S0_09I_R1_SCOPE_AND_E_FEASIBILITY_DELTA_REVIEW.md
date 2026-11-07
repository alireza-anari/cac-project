# S0-09I R1 — independent scope and E feasibility delta review

**Date:** 2026-11-07 (Asia/Tehran). **Reviewer role:** Astra Security Architecture Reviewer / Work. **Issue:** [#33](https://github.com/alireza-anari/cac-project/issues/33); parents #28/#23.

**Proposed vote: `R1_SCOPE_ACCEPTABLE_FOR_GOVERNED_RESEARCH`.** R1 faithfully turns the accepted R0 findings into explicit requirements and rejection criteria, while keeping all five E feasibility gates DESIGN_BLOCKED. Interim A remains an honest unsupported-catastrophe policy with conditional quarantine. No new contradiction requires rejection of that scope or another R0 rewrite. This vote is not a completed E contract, a finding of practical feasibility, permission to start a feasibility task automatically, PoC authorization or security acceptance.

## 1. Delta boundary and immutable provenance

| Item | Verified reference |
|---|---|
| Live main at start and review base | `724d7a418ed82d3464ec95e6f8c968a2a59df366`, matching the recorded management commit |
| Primary R1 | [`docs/architecture/S0_09I_R1_SCOPE_AND_E_FEASIBILITY_GATES.md`](https://github.com/alireza-anari/cac-project/blob/724d7a418ed82d3464ec95e6f8c968a2a59df366/docs/architecture/S0_09I_R1_SCOPE_AND_E_FEASIBILITY_GATES.md) |
| R1 Git blob / last modifying commit | `4757da6189f1a5ec2746f116754640aa02b62af0` / `fd4313ac615ce90137cd8979ace2d12e572a905d` |
| Why main is newer than the file commit | Main724d7a4 changed `docs/SOURCE_ARTIFACTS.md`, not the R1 document |
| Accepted R0 review reused | [Draft PR34](https://github.com/alireza-anari/cac-project/pull/34), exact head `5e903c26f43ea1cba52770ecedc6925b8257b9f5`; [independent report](https://github.com/alireza-anari/cac-project/blob/5e903c26f43ea1cba52770ecedc6925b8257b9f5/docs/security/S0_09I_R0_ROOT_CATASTROPHE_READ_ONLY_REVIEW.md) |
| Management acceptance / delta commission | [Issue33 comment6708799455](https://github.com/alireza-anari/cac-project/issues/33#issuecomment-6708799455) |
| R0 document unchanged | Blob `34deb449a7da357fbcb771c366cfcb65350259af`; Git comparison from prior main `e3f72ea9a1e355a574c52b12c3ae4fed6464ab01` to current main has no R0-file difference |

This is a focused document comparison against the accepted five P0, three P1 and one P2 findings. It does not repeat the R0 foundational review, reopen H implementation or independently rerun earlier evidence. Methods: reading R1, accepted review/management statements and read-only Git/GitHub provenance, path-filter and diff checks. No code, SQL, migration, workflow, test, CI or PoC was changed or executed. No dependencies, infrastructure, restore, key enrollment or experimental control were invoked. No previous PR was merged or copied into this branch.

## 2. Three distinct decisions

| Decision layer | R1 delta result | What is still missing |
|---|---|---|
| **Requirements/acceptance definition** | Substantially addressed: terminal-root threat enumeration, two recovery capabilities, explicit ordering/cut obligations, all-route stop condition and resource-continuity prohibition are DESIGN_SPECIFIED. | This is a requirements contract, not a fully defined executable protocol/state machine. G3 explicitly demands that later deliverable. |
| **Practical implementability** | Not established. Candidate families are research categories, not evidenced deployable solutions. | Named terminal primitive, actual custody/enforcement architecture, recoverable journal bodies, transition model and defensible operational/economic budgets. All G1–G5 remain DESIGN_BLOCKED. |
| **Security proof** | SECURITY_UNPROVEN / NOT_RUN for E and majority catastrophe. | No new mechanism or empirical evidence is supplied by this delta review. R1 cannot convert any gate to PASS. |

“Acceptable for governed research” therefore means management can consider a separately scoped documentation/feasibility proposal. R1 §8.3 still requires an explicit management vote for that follow-on work. It does not mean an implementation backlog item, E oracle or majority-restore test may now be launched.

## 3. P0-to-gate delta matrix

The status “addressed as a requirement” does not close the original finding. Every row remains a P0 blocker for an actual E/catastrophe-recovery claim.

| Original finding → gate | R1 change and independent assessment | Trust premise / remaining design evidence | Disposition |
|---|---|---|---|
| **I-P0-01 → G1**, terminal E continuity | §2 names the current irreversible/monotonic authority fact and enumerates reset/reimage/firmware/backup, credentials, custody rotation, replacement/rebootstrap, partition and verifier-root loss. It hard-rejects shared restorable control and arbitrary higher-sequence attestation. This addresses the missing boundary rather than hiding another assumed root. | A concrete surviving fact **and mandatory verification/enforcement root** must exist outside the claimed rollback envelope. Which primitive and independent actors supply them remains unnamed. If E and its enforcement roots can coherently rewind, a rule saying “deny after loss” cannot detect that loss by itself. R1 §1 correctly retains that unsupported case. | Boundary/rejection criteria DESIGN_SPECIFIED; G1 DESIGN_BLOCKED; mechanism SECURITY_UNPROVEN / NOT_RUN. |
| **I-P0-02 → G2**, complete obligations versus digest | §3 explicitly separates DETECT_AND_DENY from RECONSTRUCT_AND_CONSERVATIVELY_AUTHORIZE. It requires resource/operation/transaction identities, policy, tombstones, barriers, complete pending set and checkpoint/retention completeness. A gap is not an empty set; a log root cannot infer a local effect. This directly addresses the R0 distinction. | Authentic complete bodies and absence/ancestry evidence at a current E index, or continued exclusion without them. A complete pending set containing UNKNOWN is **not** a settled set; replay alone never permits a successor or clears an orphan. Actual data availability, retention and safe reconstruction remain undesigned. | Capability distinction DESIGN_SPECIFIED; G2 DESIGN_BLOCKED; reconstruction SECURITY_UNPROVEN / NOT_RUN. |
| **I-P0-03 → G3**, cross-root/PG order | §4 rejects “two reads” and “R then E” as atomicity proof. It specifies durable operation continuity before first usable permit, original-key/digest retry, ordered first-use/revoke, exact known outcome before close, and named divergent/lost-ACK cuts. These are falsifiable model obligations, not a working bridge. | A future candidate must supply the single authority linearization rule, legal state transitions, authenticated status-resolution semantics, previous-head constraints and exact outcome bindings. No such state machine/transport/2PC/lease is selected. Existing grants may continue only behind preserved exclusion of successor READY. | Ordering/cut requirements DESIGN_SPECIFIED; G3 DESIGN_BLOCKED; protocol and executable schedules NOT_RUN. |
| **I-P0-04 → G4**, mandatory current admission | §5 explicitly covers SQL/Issuer/RLS, private/pre-E/C-only routines, role/ACL/build floors, active/prepared work, existing PgBouncer clients/backends, alternate/admin routes and restored enrollment. Any unsupported bypass becomes a hard stop, not a tolerable warning. Currentness cannot be self-certified by a restored verifier. | Independent admission/enforcement must actually survive and cover every supported route, including privileged compromises if claimed. A network/UI status, optional E client check or NOLOGIN alone does not prove coverage. R1 correctly excludes or demands constraints on common-admin/DB-superuser/observer powers. | Stop condition DESIGN_SPECIFIED; G4 DESIGN_BLOCKED; real isolation/custody SECURITY_UNPROVEN / NOT_RUN. |
| **I-P0-05 → G5**, resource continuity | §6 now explicitly includes new root, namespace, key, actor, database incarnation, cluster ID and manifest. It requires a resource-bound predecessor link and carried unresolved history; re-genesis cannot restore READY after unverifiable catastrophe. Human/fence/hardware receipts do not settle old effects. This directly closes the wording gap as a prohibition. | A future model must identify the same protected resource and effects across aliases/clones/incarnations, preserve obligations and independently establish any truly new-resource isolation. Renaming or changing credentials is not evidence of isolation. No root-replacement/resumption procedure has been proved. | No-laundering rule DESIGN_SPECIFIED; G5 DESIGN_BLOCKED; implementation/security NOT_RUN. |

G1–G5 are interdependent. A current protected counter without G2 cannot reconstruct obligations; G2 without G3 can release authority in the wrong order; G3 behind a bypassing old route fails G4; a fresh identity escaping those obligations fails G5. No individual gate's wording is evidence that the end-to-end recovery path exists.

## 4. G3 falsifiability and interpretation limits

R1 defines enough **accept/reject obligations for later model review**, not a fully specified test suite. A proposed model must reject the unsafe result at each cut below; this review did not execute the cuts or authorize them.

| R1 cut / condition | Required observable model property | What cannot be inferred |
|---|---|---|
| R OPEN committed; E publication unacknowledged | No usable permit without required current durable continuity; retry/status tied to original operation/digest | No reply does not mean absent E commit or permission to allocate a replacement epoch |
| E OPEN committed; response lost | Exact current status resolution or continued exclusion; no duplicate altered-intent operation | Timeout is not ABORT and is not evidence of an empty pending set |
| Grant/revoke race; old reply delayed | Post-revoke first grant denied; earlier valid grant remains accounted for and successor excluded through possible local effect | Equal heads observed once do not recall an earlier COMMIT packet |
| E ahead, R ahead, or E stale after failover | No new authority on unverifiable disagreement; only a fully specified current-status/replay path can recover agreement | Responsiveness, a signature or a larger sequence alone does not establish legal latest state |
| Local PG COMMIT/ABORT ACK or E/R CLOSE reply lost | Preserve exclusion until exact durable status is positively established under the candidate's current authority | An idle backend, lost session or apparently reconstructed row is not outcome proof |
| Incomplete checkpoint/suffix, missing mapping or tombstone | Detection may block; reconstruction cannot claim completeness | Restored epoch/head is not a complete operation inventory |
| New root/namespace with old resource obligations | No successor READY through a reset/renaming shortcut | New identity and human approval do not erase old effects |

Two readings must remain explicit in the future candidate; neither changes R1's scope vote:

1. **Lost ACK is not permission for Lane3.** The phrase “unless status is positively established” (§4.3) must distinguish a client learning an already authoritatively recorded exact CLOSED outcome from a new attempt to reconcile a durably unresolved UNKNOWN. The former is acknowledgment/status recovery; the latter remains unauthorized Lane3. R1 §§3,6,9 prohibit orphan clearing. No transition from unresolved UNKNOWN to released authority is introduced by this review.
2. **G4 does not erase legitimate earlier grants.** Its stop rule concerns unadmitted/bypassing routes. A valid pre-revoke grant that G3 still accounts for may finish while successor remains excluded. Conversely killing sessions or blocking new connections cannot justify forgetting that grant or its possible effects. A candidate must make these categories explicit, rather than claim that every old transaction necessarily stopped.

Likewise §3's detection-only NOT_READY means no resumption from incomplete evidence. A later authenticated reconstruction is a separate gated capability, not automatic mode promotion. Even full replay may merely reproduce unresolved holds and indefinite exclusion. There is no availability or recovery-success claim in this safety-only requirement.

## 5. Retained P1/P2 assessment

| Finding | R1 coverage / status | Residual requirement before an implementation request |
|---|---|---|
| **I-P1-01**, trustworthy incident trigger/isolation | §7 retains silent responsive rewind versus unavailable majority versus intact restart, route audit and evidence-based quarantine. Addressed as a requirement; SECURITY_UNPROVEN / NOT_RUN. | Name who can signal/verify each transition, independent evidence and complete coverage. A requested isolation must never be relabeled verified quarantine. If no surviving enforcement exists, use GLOBAL_FAIL_CLOSED_NOT_ESTABLISHED / SECURITY_INCIDENT. |
| **I-P1-02**, local outcome/observer custody | §§3–5,7 require exact PG incarnation/transaction/effect receipt, observer/admin restore powers and prepared-state treatment. Addressed as a dependency; SECURITY_UNPROVEN beyond H / NOT_RUN. | Supply candidate-specific outcome/status and custodian model, including observer rollback/forgery and lost-ACK terminology above. H's trusted observer, signer retirement and known local outcomes are not root-catastrophe custody proof. |
| **I-P1-03**, economics/availability | §§2,4,7 require two unapproved continuity families, custody/failure-domain diagrams, replacement ceremonies, request/retention growth and outage accounting; no guessed numerical SLA. Adequate research requirement; NOT_RUN / unpriced. | A named feasibility proposal may conclude neither family qualifies. “Implementable” in the requested comparison is not evidence that either is currently feasible. Compare A's potentially indefinite outage/incident costs against B/C's additional online, serialized-state, storage and independent-operation dependencies; measure only after separate authorization. |
| **I-P2-01**, labels/provenance | §§1,7,9 retain conditional enforcement and explicit statuses. Documentation clarification substantively addressed. | Preserve qualifiers in future receipts/backlog: scope acceptance, contract specification, practical feasibility and security proof are different. Prior H inventory remains169+51=220 separate-suite methods plus2 artifact-only methods; five mutation controls are not new R1 tests. No evidence status is upgraded here. |

No new observed P0/P1 vulnerability is alleged: no mechanism was executed. The five original P0 blockers, three operational P1 obligations and their proof limits remain open. These are clarified requirements, not closed findings.

## 6. Preserved scope and governance

| Item | Disposition after this delta review |
|---|---|
| Interim option A | Sufficiently explicit unsupported-majority/joint-restore boundary; quarantine required only where independent mandatory enforcement actually survives |
| E / majority R catastrophe security | SECURITY_UNPROVEN / NOT_RUN; all G1–G5 DESIGN_BLOCKED; no implementation approval |
| Actual policy-retirement transition | NOT_RUN; policy mismatch and signer retirement remain different evidence |
| Literal old Raft snapshot/WAL import or rejection | NOT_RUN; fresh learner replacement is not a substitute |
| S0-09D C-only rollback | FAIL_SECURITY, unchanged |
| H quorum-survival results | Previously accepted bounded non-restored-majority evidence only; no majority-rollback inference and no rerun |
| Lane3 orphan UNKNOWN release | BLOCKED / NOT_RUN; no status-query, namespace, clock, hard-fence or operator-approval shortcut |
| New tests, CI, PoC, infrastructure, Production | Not authorized or performed by this review |

Recommendation: **R1_SCOPE_ACCEPTABLE_FOR_GOVERNED_RESEARCH**. Further documentation may be proposed to management under R1's explicit decision gate. No gate becomes PASS; no concrete E candidate has been found feasible; no complete R/E/PG protocol or catastrophe-security proof is accepted. A future concrete candidate still needs a specified contract and its own adversarial review; that is not a reason to repeat the accepted R0 review. The alternative UNSUPPORTED_SCOPE_INSUFFICIENT is not warranted because R1 explicitly retains the no-global-denial case, enforcement-dependent quarantine, security incident and indefinite-denial limits.

This Draft PR adds only this document against current main. Verification is documentation/provenance/diff checking only, not security testing. Main's existing workflow filters were inspected read-only; this document path is outside their selected paths. Any final GitHub checks are reported separately and must not be described as empirical E proof.

All previous PRs, including34, remain Draft/unmerged. Issues33/28/23 and Gate9 remain OPEN; SOURCE-001/GATE-SOURCE BLOCKED; NEW_IMPLEMENTATION_EXPERIMENTAL / PROTOCOL_PROPOSED retained. No APR033–036, canonical source/baseline, Sprint0, real identity/MFA/onboarding, vendor/KMS/algorithm choice, Production or merge approval. The independent review cannot grant the separate management authorization it requires.
