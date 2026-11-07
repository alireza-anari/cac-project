# S0-09I R0 — independent root-catastrophe architecture review

**Date:** 2026-11-07 (Asia/Tehran). **Role:** Astra Security Architecture Reviewer / Work. **Delivery:** Issue [#33](https://github.com/alireza-anari/cac-project/issues/33); parents #28/#23.

**Proposed vote: `R0_SCOPE_ACCEPTABLE_FOR_FURTHER_DESIGN`.** The selected interim policy A is defensible as an explicit unsupported-recovery boundary with conditional quarantine. It is not an implemented universal fail-closed guarantee. E remains a research requirement, not a demonstrated root. This vote allows management to consider further documentation/design only; it grants no PoC, Lane2/Lane3 execution, protocol acceptance or Production authority.

Five P0 design obligations, three P1 obligations and one P2 clarification remain below. These are unresolved conditions on stronger recovery claims, not newly observed exploits. Accepting the scope does not close any finding or approve option B. A future E/majority-recovery proposal requires targeted contract refinement before any separate execution decision. Rejecting R0 outright would conflate its honest unsupported-policy choice with a false claim that catastrophe recovery already works.

## 1. Source and review provenance

| Item | Verified reference |
|---|---|
| Live main at review start | `e3f72ea9a1e355a574c52b12c3ae4fed6464ab01`, matching the management-provided SHA |
| Primary document | [`docs/architecture/S0_09I_ROOT_MAJORITY_CATASTROPHE_DESIGN_R0.md`](https://github.com/alireza-anari/cac-project/blob/e3f72ea9a1e355a574c52b12c3ae4fed6464ab01/docs/architecture/S0_09I_ROOT_MAJORITY_CATASTROPHE_DESIGN_R0.md) |
| Primary document Git blob | `34deb449a7da357fbcb771c366cfcb65350259af` |
| Last commit modifying that file | `b5ff74a86920e6ab5eb06e7dccf612cffe696738`; the newer main commit changed `docs/SOURCE_ARTIFACTS.md`, not R0 |
| Management issue | Open Issue33 and management comment [6707610963](https://github.com/alireza-anari/cac-project/issues/33#issuecomment-6707610963), explicitly no code/test/CI execution authorization |
| H management ruling read | [`S0_09H_ARCHITECTURE_RULING.md`](https://github.com/alireza-anari/cac-project/blob/e3f72ea9a1e355a574c52b12c3ae4fed6464ab01/docs/architecture/S0_09H_ARCHITECTURE_RULING.md), last file commit `57a723f1f8a441011c23e85cb5bbacb2428fdfd5` |
| Accepted H evidence boundary | PR32 head `b32416c799160f0e5957506d58254a693cbc231f`, final [Issue31 receipt](https://github.com/alireza-anari/cac-project/issues/31#issuecomment-6706010513); conditional current non-restored 3/5 majority only |

Method: critical document inspection, read-only Git/GitHub provenance checks and official technical reference reading. No executable code, SQL, migration, workflow or test was modified or run. No dependencies installed, CI dispatched, cluster restored, key enrolled or security experiment performed. The hypothetical traces below are reasoning, not empirical evidence. H results are prior management-accepted evidence, not independently rerun or recertified by this mission. This is an independent review of management's R0 proposal, not external operational/custody certification.

## 2. The support policy and impossibility boundary

R0 §§1,3,4,7 correctly distinguish an unavailable quorum from a responsive rewound quorum. A valid response or new signature from a restored old signer can be authentic and still describe obsolete authority. The document explicitly withholds a global denial guarantee when all enforceable newer facts are gone. That qualification must survive into every runbook and status label.

The indistinguishability argument is defensible under an explicit observation model:

| World | Past events | Inputs still available to the authorization decision |
|---|---|---|
| H1 | Epoch1/A is genuinely latest; no later pending work | R head1, old allowed keys/policy, old guard state and corresponding PG/W observations |
| H2 | Epoch2/B or a newer OPEN was acknowledged, then all decision-relevant evidence was erased, rewound, inaccessible or not consulted | The same head1, allowed keys/policy, guard state and observations |

If request, available trusted state, identity/key policy and enforcement inputs are indistinguishable, a decision procedure cannot infer the missing event. Fresh nonces authenticate a fresh exchange with the old state; they do not recreate a lost historical fact. Random choices cannot reliably recover which history occurred. This is a conditional indistinguishability argument, not a formal proof against all possible external observations.

A majority rollback does **not automatically** erase every trace. A surviving newer voter, external client receipt, independent current policy record, protected counter, effect record or full operation journal may distinguish histories. It must be authentic, relevant, available and mandatory in the decision. A merely current executable verifier that remembers no newer authority fact is insufficient. A surviving receipt may prove that the restored head is stale without proving that the supplied replacement history is complete. Stale rollback to an intermediate head can forget OPEN or policy changes even when owner/epoch did not change.

Normal restart from intact current persistent state must not be confused with restoration of unverified older state. Loss of availability, proven loss of current history and an undetected responsive rewind are different incidents. Policy A can require stopping service after a trustworthy incident signal; it cannot promise to detect every silent rollback. Without an enforceable surviving boundary, record `GLOBAL_FAIL_CLOSED_NOT_ESTABLISHED`, not verified quarantine.

## 3. Claim disposition

`DESIGN_SPECIFIED` means a rule is stated, not implemented or proved. `SECURITY_UNPROVEN` means a necessary assumption/invariant has no new security evidence. `DESIGN_BLOCKED` means a stronger recovery/authorization claim cannot be accepted without a concrete contract. `NOT_RUN` means no execution evidence is supplied here.

| R0 claim / obligation | Status in this review | Basis / limit |
|---|---|---|
| No automatic authority resurrection from unverified majority restore | DESIGN_SPECIFIED | §§1,4,7 define a support restriction; actual universal enforcement is not established |
| Conditional independently enforced quarantine | DESIGN_SPECIFIED / SECURITY_UNPROVEN | Correct conditional wording; incident detection, coverage and custody still required |
| Guaranteed fail-closed after joint majority/old-verifier restore | DESIGN_BLOCKED / NOT_RUN | R0 explicitly does not claim this; no surviving newer fact/enforcement root is supplied |
| Indistinguishability with all relevant inputs restored | DESIGN_SPECIFIED reasoning | Valid conditional argument above, not an executed attack or unconditional impossibility claim |
| E preserves a fresh latest complete authority commitment | SECURITY_UNPROVEN / DESIGN_BLOCKED | §5 is a necessary requirement list; no terminal primitive or recovery mechanism is specified |
| E survives its own rollback, replacement and shared-control compromise | DESIGN_BLOCKED / NOT_RUN | Independence is a security premise, not established by naming E or adding another quorum |
| Complete OPEN/UNKNOWN, tombstones, policy and actor binding | DESIGN_SPECIFIED requirement / SECURITY_UNPROVEN | Inclusion stated; durable publication, availability and lifecycle semantics remain unspecified |
| R/E/PG staging makes authorization atomic | DESIGN_BLOCKED / NOT_RUN | §5.4 expressly labels staging a research sketch; see counterexamples |
| No successor while old transaction may still commit | DESIGN_SPECIFIED invariant / SECURITY_UNPROVEN for E | H gives bounded predecessor evidence, not a proof across catastrophe/E transitions |
| Current policy/key/bootstrap enforcement on every old route | DESIGN_SPECIFIED requirement / DESIGN_BLOCKED realization | Old code can omit an optional E call; independent mandatory enforcement is essential |
| Unknown remains blocked even after hard fence or outage | DESIGN_SPECIFIED; Lane3 BLOCKED | No clearing procedure proposed or authorized; indefinite exclusion remains possible |
| H current-majority W restore/fresh learner replacement | Prior BOUNDED_OBSERVED_PASS only | No transfer of that result to majority rollback or genuine stale snapshot import |
| Actual policy retirement; literal old Raft snapshot/WAL import | NOT_RUN | Signer retirement and fresh learner replacement do not discharge these |
| E hardware, independent custody, cost/capacity/RPO/RTO | NOT_RUN / not measured | No product, quantitative SLA or recovery cost accepted |

## 4. Findings matrix

| ID / severity | R0 locus and technical reason | Required trust assumption | Proof status | Recommended refinement, before stronger claims |
|---|---|---|---|---|
| **I-P0-01** — terminal continuity is not instantiated | §§3,5.1,6: E with the same restorable storage/admin/backup or enrollment control reproduces R's problem. An HSM-held key or a current signed nonce does not prove newest state. | A specific newer fact and its verification/enforcement root survive the exact claimed catastrophe. | SECURITY_UNPROVEN / DESIGN_BLOCKED | Identify E's primitive, failure envelope, who can reset/restore/enroll it, what survives E loss and when recovery is permanently unsupported. Do not terminate the argument with an unexplained additional witness/quorum. |
| **I-P0-02** — a commitment is not complete recoverable operation history | §5: a digest can detect disagreement while its committed OPEN/UNKNOWN bodies are unavailable. Epoch alone also misses same-epoch operations. | Authenticated append/state-transition semantics and sufficient retained data or permanently conservative exclusion. | DESIGN_SPECIFIED inclusion; availability/semantics SECURITY_UNPROVEN | Separate detection-only denial from usable reconstruction. Define complete pending set, identities, proofs, tombstones and retention/checkpoints. Missing body or proof means blocked, never empty. |
| **I-P0-03** — R/E checks do not make the PG commit boundary atomic | §5.3–5: staging plus dual-head match leaves interleavings among E publication, grant, revoke, CLOSE and local COMMIT. | One defensible ordering of grant/revoke/hold transitions and trusted exact outcome observation; no authority on timeout. | DESIGN_BLOCKED / NOT_RUN | Specify which transition linearizes authority, durable hold-before-permit, validated previous-head/CAS rules, idempotency and every lost-ACK cut. Carry old holds until positive exact outcome/CLOSE, including after either root restarts. |
| **I-P0-04** — current E is ineffective behind a restored bypassing verifier | §§5.2,6,7: old SQL/issuer/pool routes can accept obsolete policy or omit E entirely; a verifier cannot establish its own currentness from its restored trust store. | Independent current admission/enforcement and policy trust, covering all supported routes and surviving the same rollback. | DESIGN_BLOCKED / NOT_RUN for catastrophe | Specify trusted bootstrap, minimum policy/build/key epochs, current E identity, retired-writer/actor rejection, route closure and incumbent-session/pool treatment. Retired-policy restoration is not covered by H signer retirement. |
| **I-P0-05** — root re-enrollment must not launder unknown work | §§5.6,7: new root/namespace/actor identities can appear to have zero OPEN while previously authorized work on the same protected resource can still commit or already have effects. | Continuity of resource authority and unresolved obligations across every incarnation/enrollment. | Existing prohibition DESIGN_SPECIFIED; replacement contract DESIGN_BLOCKED | Explicitly forbid new genesis/namespace/policy/key enrollment from granting authority over resources with unresolved predecessor obligations. Human approval/hard fence alone is insufficient. No Lane3 mechanism is designed or authorized here. |
| **I-P1-01** — quarantine needs a trustworthy trigger and coverage receipt | §§1,6,7: an operator-requested isolation or responsive endpoint is not proof of effective denial; silent rollback may not trigger the incident machine at all. | Surviving incident/control plane, accurate route inventory and independently verifiable isolation. | SECURITY_UNPROVEN / NOT_RUN | Define evidence to enter ROOT_SUSPECT/VERIFIED_QUARANTINED/REVIEWED_CURRENT_HEAD, distinguish intact restart from stale restore, and retain GLOBAL_FAIL_CLOSED_NOT_ESTABLISHED if any path cannot be excluded. |
| **I-P1-02** — durable outcome and observer custody remain a dependency | §§5.5,6: authenticated observer testimony is not proof if the observer or PG incarnation/effect history can be coherently rewound or forged. | Honest independent outcome observer and exact durable PG outcome/resource identity; privileged compromise excluded unless constrained. | SECURITY_UNPROVEN beyond H's bounded observer | List issuer/runtime/observer/operator powers; define operation/DB-incarnation/outcome evidence and ambiguous-reply behavior. Neither idle backend, reconstructed row state nor lost ACK implies ABORT. Preserve prepared-transaction exclusion unless separately modeled. |
| **I-P1-03** — economics/availability cannot be ranked by replica count | §§4,6,8: E adds synchronous freshness/serialization, durable retention, operational ceremonies and another dependency; A may incur indefinite outage. | A deployable genuinely separate custody/failure-domain model and explicit availability objectives. | NOT_RUN / unpriced | Use the qualitative comparison below; request future workload/custody/recovery budgets before technology selection. No cost/latency/RPO/RTO numbers inferred from H CI timings. |
| **I-P2-01** — support labels and provenance must retain qualifiers | §§1,8,9; Issue33 exit shorthand: UNSUPPORTED_FAIL_CLOSED can lose its conditional meaning in downstream summaries. Counts and authoring-time pending records also need their ruling/receipt context. | Reviewable immutable evidence and distinct policy/observation/authorization statuses. | DESIGN_SPECIFIED, documentation clarification | Always pair unsupported restore with conditional quarantine/global-denial-not-established. Keep H 169+51=220 separate-suite cases plus2 artifact methods; preserve actual policy retirement/stale import NOT_RUN and D FAIL_SECURITY. Version claims by immutable SHA; never count this review as new test proof. |

## 5. Cross-root counterexamples to resolve in later design

These are hypothetical schedules, not experiments, implementations or a selected replacement protocol.

| Cut / trace | Why the R0 sketch alone is insufficient | Required invariant, not implementation approval |
|---|---|---|
| R records candidate OPEN, E has not acknowledged it; R fails/restores | Treating the candidate as a usable grant creates work E may not retain. | No first permit before E durably accounts for the exact operation; incomplete staging cannot become permission. |
| E accepts OPEN, its reply is lost, coordinator restarts | Missing reply does not prove that E aborted or has no pending work. | Persist exclusion/idempotency and positively resolve exact state; if not resolvable, remain blocked. |
| R and E are read equal; a revoke/takeover races a delayed grant or in-flight PG COMMIT | Agreement at an instant does not serialize subsequent effect execution or recall an already issued COMMIT. | Durable holds and defined first-use/revoke order must exclude successor throughout the possible old effect, not just at the freshness check. |
| CLOSE becomes effective in E before positive exact local outcome, then PG commits | Successor could see an empty pending set while an old commit still succeeds. | No effective hold removal until trustworthy exact durable outcome and authorized close. A hard fence does not replace outcome proof. |
| E publishes a later sequence with a lower/incomplete pending set from stale R | Increasing a counter and signing a digest can still bless forgotten OPEN or obsolete policy. | Validate ancestry and allowed state transitions, actor/writer admission and unresolved obligations; do not accept arbitrary latest-looking digests. |
| E commits a new owner, R or the verifier restarts behind; an old signed decision arrives | A fresh-looking signature or retry can refer to a retired root/actor or an obsolete grant. | Bind namespace/root/actor incarnation, resource, operation, policy, exact transaction and replay context to current E authority; define in-flight continuation explicitly. |
| E retains a head commitment; corresponding full journal/checkpoint is missing or suffix withheld | Freshness disagreement can justify denial, but cannot enumerate or discharge all unknown obligations. | Distinguish detect-and-stop from reconstruct-and-resume; never substitute an empty set or audit-store listing for completeness. |

R0 correctly treats outage, lost ACK and unknown local effect as different events. “Deny new permits during E outage” does not imply that every earlier grant or in-flight PG COMMIT has stopped. Similarly, two independently linearizable stores do not automatically provide one atomic transaction across both stores and PostgreSQL. The refinement must define safety under disagreement rather than assume a distributed transaction already exists. This review selects neither 2PC, leases nor another mechanism. An added timeout cannot safely convert unknown to abort.

## 6. E identity, key/policy continuity and old-route enforcement

E can add security only if it retains a relevant fact outside the R restore envelope and current enforcement must consult it. A separately named database/account/quorum whose state, reset authority or verifier can be restored together with R adds no such argument. A genuinely narrower failure envelope is legitimate, but must explicitly stop service when E's required continuity fact is lost. The design need not claim recovery from destruction of every possible root; it must identify where its trust argument terminates.

Keys, freshness, policy and effect history are distinct. Protecting a key against extraction does not preserve the pending journal or establish newest sequence. Retiring a signer is not the same as retiring a verifier policy, trust-root set, permitted actor or administrator's enrollment authority. Recoverable old private keys need not be accepted if a mandatory independent current policy reliably rejects them; conversely key destruction alone does not repair an old verifier with a valid-looking restored history. A nonce proves participation in an exchange, not nonrollbackable storage. No clock/TTL exception is accepted for OPEN_UNKNOWN.

The route inventory must include fresh issuer entry, direct SQL/RLS, old C-only and pre-R routines, private/security-definer paths, active transactions, existing PgBouncer server/client sessions, alternate listeners/local/admin entry and restore/re-enrollment procedures. Network admission of new connections alone does not revoke an existing pooled backend. NOLOGIN alone does not establish that incumbent transactions cannot finish. Physical/root/DB-superuser compromise remains outside the H model unless a new independent enforcement contract constrains it. No untrusted verifier may self-certify its image or upgrade its own trust floor from the restored database.

## 7. Qualitative options and operational economics

| Option | Security contribution and independence | Operational complexity / cost drivers | Availability and disaster outcome |
|---|---|---|---|
| **A — unsupported majority restore** | Honest refusal to promise recovery from unverifiable history. Meaningful quarantine still depends on surviving enforcement/control evidence. | No new E serialization service, but route isolation, backup controls, audits and incident expertise are not free. Outage losses may dominate savings. | Indefinite downtime is possible. Undetected joint restore is not guaranteed to stop. Intact current-state restart remains distinct from stale recovery. |
| **B — independent online E** | Could detect responsive stale R if fresh latest state, admission and trust actually survive outside its rollback domain. Otherwise moves the problem. | Separate administration/backup/enrollment and policy custody; online decisions, durable state/hold serialization, replay/checkpoint/tombstone storage, key rotation and incident procedures. Exact request budget depends on the missing contract. | Loss/ambiguity must block new authority; old permits require durable holds. Shared power/network/cloud identity can remove claimed independence. Restoring E itself remains a new catastrophe boundary. |
| **C — protected counter/hardware or independent witness plus full log** | Candidate primitive for B, not a complete E. Requires binding to namespace, head, policy and full pending obligations; a counter alone cannot establish the missing set. | Physical inventory, anti-reset/clone guarantees, provisioning, replacement/destruction ceremonies and availability of bound data. No device/product selected or certified. | A surviving fact may allow detection-only denial while log data is unavailable. Loss/replacement cannot silently create empty authority or erase UNKNOWN. |
| **D — immutable audit store / bumped snapshot alone** | Useful for preservation/incident reconstruction; no standalone proof of latest complete head or current enforcement. | Storage/retention, indexing, authenticated completeness/provenance and retrieval costs remain. Adding an online authoritative witness makes it a B-like design. | A consistent older prefix may be returned. Restored state or cache invalidation is not safe CAC authority recovery by itself. |

There is no justified numerical cost, latency, throughput, RPO/RTO or HA ranking. A later design can budget operation rate, E-decision/commit dependencies, retention/checkpoint verification, incident staffing, cross-domain connectivity and failure-induced downtime, with explicit evidence sources. H's single-host results measure none of the required real administrative independence.

## 8. Refinement deliverables and proof boundaries

The next permitted deliverable can be documentation defining: (a) E's terminal continuity primitive and reset/loss boundary, (b) who can restore each root, guard, policy and key, (c) mandatory all-route bootstrap/admission evidence, (d) canonical event/operation/hold and resource-incarnation continuity, (e) the R/E/PG ordering and ambiguous-cut table, and (f) honest quarantine/outage/economics acceptance criteria. Those are obligations extracted from R0, not a newly selected implementation. A concrete protocol, state machine and independently falsifiable future proof plan require a separate management decision. No future test is dispatched by this report.

| Preserved item | Disposition |
|---|---|
| Actual policy retirement, including restored earlier verifier-policy trust | NOT_RUN; mismatched policy input or signer retirement is insufficient |
| Literal old Raft snapshot/WAL import or protocol-correct rejection | NOT_RUN; fresh nonvoting learner replacement is a different completed H path |
| Majority restore/joint obsolete verifier restore/physical clone/custody | NOT_RUN / SECURITY_UNPROVEN; no new Lane2 authorization |
| Exact Raft ACK crash cuts, compaction/retention, multi-domain partitions | NOT_RUN in this review; listing obligations does not authorize execution |
| Old S0-09D C-only rollback | FAIL_SECURITY, unchanged |
| Lane3 OPEN_UNKNOWN reconciliation/clearing | BLOCKED; no timeout, fencing, operator signature or new namespace shortcut |
| H evidence | Prior bounded current non-restored-majority observation only; no majority rollback conclusion |

## 9. Official references and their limited use

References checked during this document review; these are product/background facts, not proof of CAC's proposed E or catastrophe safety:

- [etcd v3.6 recovery](https://etcd.io/docs/v3.6/op-guide/recovery/): snapshot restoration starts a new logical cluster with changed member/cluster identity; revision bumping addresses restored revision/cache behavior. These procedures do not reconstruct missing later CAC authority events.
- [etcd API guarantees](https://etcd.io/docs/v3.6/learning/api_guarantees/): KV operations have atomic ordering/durability guarantees; watch delivery is not a substitute for a current linearizable decision, and a disrupted reply can leave completion unknown. These guarantees are not a cross-R/E/PG commit protocol or a guarantee across destructive state rewind.
- [PostgreSQL17 COMMIT](https://www.postgresql.org/docs/17/sql-commit.html) and [two-phase transactions](https://www.postgresql.org/docs/17/two-phase.html): local commit and optional externally managed prepared transactions have defined database semantics. They do not supply an E bridge automatically. No prepared-transaction experiment or new 2PC choice is proposed here.
- [NIST SP800-57 Part1 Rev5](https://csrc.nist.gov/pubs/sp/800/57/pt1/r5/final): general key lifecycle/protection guidance. It neither certifies E nor selects a device or guarantees policy freshness.

## 10. Management disposition

Recommend **R0_SCOPE_ACCEPTABLE_FOR_FURTHER_DESIGN**, accepting the honesty and boundaries of interim A and keeping B/C research-only. No claim in this review changes an unresolved E obligation to SECURITY_PROVEN. Do not describe this vote as approval to implement an E oracle, restore an R majority, clear an orphan or start another Lane2 PoC.

This Draft PR changes only this review document. No tests/CI/security experiments were run. Existing main workflow path filters were inspected read-only; this document path does not select their execution. Final GitHub PR/head/changed-file status and any reported checks must be distinguished from security-test results.

Issue33/#28/#23 and Architecture Gate9 remain OPEN; SOURCE-001/GATE-SOURCE remain BLOCKED. Earlier PRs remain Draft/unmerged. APR033/034/035/036 unchanged. NEW_IMPLEMENTATION_EXPERIMENTAL / PROTOCOL_PROPOSED remains. No Production, canonical baseline, historic source recovery, identity/MFA/onboarding integration, Sprint0 completion or security-protocol ratification.
