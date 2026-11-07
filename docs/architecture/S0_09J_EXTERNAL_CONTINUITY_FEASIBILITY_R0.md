# CAC — S0-09J External Continuity Feasibility R0

**Date:** 2026-11-07
**Role:** Astra Security Architecture Research / Work
**Execution:** [#36](https://github.com/alireza-anari/cac-project/issues/36); architecture [#33](https://github.com/alireza-anari/cac-project/issues/33), [#28](https://github.com/alireza-anari/cac-project/issues/28), [#23](https://github.com/alireza-anari/cac-project/issues/23)
**Disposition:** DOCUMENTATION_ONLY / FEASIBILITY_RESEARCH / NO_POC_AUTHORIZATION
**Recommended vote:** **`NO_CREDIBLE_E_CANDIDATE_KEEP_A`**
**Origin:** CAC-NEW-ORIGIN-S0-07 / NEW_IMPLEMENTATION_EXPERIMENTAL / PROTOCOL_PROPOSED.

## 1. Decision and its limits

Neither evaluated family currently qualifies as a CAC external continuity authority. Retain interim Option A: catastrophe recovery from a coherently rewound R majority is unsupported. E1 lacks an identified terminal latest-head survival and custody mechanism. E2 has relevant documented physical monotonic-counter semantics, but a counter is not an authenticated legal authority transition, a complete journal, or independently mandatory enforcement. Both also fail the present G4 qualification: no evidenced current control plane covers every jointly restored SQL/issuer/verifier/pool route. These are early rejection grounds; favorable assumptions about later gates do not repair them.

This is a rejection of **current end-to-end qualification**, not a proof that every external continuity design is impossible. No deployable product was evaluated or selected. The sources establish useful primitive properties, not a CAC deployment, physical independence, or a security proof. Conditional sketches below identify what additional evidence would change this assessment. They are deliberately not promoted to `E_DETECTION_ONLY_RESEARCH_CANDIDATE` merely by assuming an unrewound E and an unbypassable verifier: those are the unresolved questions.

All five I-P0-01..05 / G1..G5 remain **DESIGN_BLOCKED**. Necessary invariants are described at research level; practical feasibility is unestablished and security is **SECURITY_UNPROVEN / NOT_RUN**. No tests, CI, active experiments, infrastructure, keys, SQL, migrations, executable code or workflows were run or changed for this study. Reading public specifications and repository documents is the evidence method. This report requests a later independent adversarial **read-only review**, not implementation authorization.

Option A is a support policy, not universal technical denial. When an independently current, mandatory guard really survives, it must deny unverifiable new authority. If all relevant enforcement can rewind, retain **GLOBAL_FAIL_CLOSED_NOT_ESTABLISHED / SECURITY_INCIDENT**. Indefinite downtime is a possible consequence even with an intact E.

## 2. Authorization, provenance and evidence method

The live main and formal ruling were read before this study. Main at the research baseline was `d6271a75bc553eb1e047a1d658bacea61706e77d`; the new documentation branch starts exactly there. Management's recorded main SHA and the live SHA matched. Main's tip modifies SOURCE_ARTIFACTS, not the ruling; these identities must not be conflated.

| Input | Immutable identity / use |
|---|---|
| [Formal ruling and J authorization](https://github.com/alireza-anari/cac-project/blob/d6271a75bc553eb1e047a1d658bacea61706e77d/docs/architecture/S0_09I_R1_REVIEW_RULING_AND_S0_09J_RESEARCH_AUTHORIZATION.md) | Last file commit `a9a407db5ccf2d785c2c2e1816df93782a85f224`; Git blob `a63ec92ed2b844b2b2502e656c3dd15de224ef8e`; no PoC authority |
| [I R1 scope and gates](https://github.com/alireza-anari/cac-project/blob/d6271a75bc553eb1e047a1d658bacea61706e77d/docs/architecture/S0_09I_R1_SCOPE_AND_E_FEASIBILITY_GATES.md) | Last file commit `fd4313ac615ce90137cd8979ace2d12e572a905d`; blob `4757da6189f1a5ec2746f116754640aa02b62af0`; normative G1–G5 criteria |
| [Accepted I R1 independent review, Draft PR #35](https://github.com/alireza-anari/cac-project/blob/9134fcf3879f04f4f99fe448bbc782284ac3a572/docs/security/S0_09I_R1_SCOPE_AND_E_FEASIBILITY_DELTA_REVIEW.md) | `9134fcf3879f04f4f99fe448bbc782284ac3a572`; scope readiness only, five P0 open |
| [Accepted I R0 independent review, Draft PR #34](https://github.com/alireza-anari/cac-project/blob/5e903c26f43ea1cba52770ecedc6925b8257b9f5/docs/security/S0_09I_R0_ROOT_CATASTROPHE_READ_ONLY_REVIEW.md) | `5e903c26f43ea1cba52770ecedc6925b8257b9f5`; finding identifiers retained |
| [Issue #36](https://github.com/alireza-anari/cac-project/issues/36) | Live execution criteria, including seven counterexamples, custody and all-route stop rules; issue text is mutable, unlike commit-pinned files above |
| [H Draft PR #32](https://github.com/alireza-anari/cac-project/pull/32) | Recorded head `b32416c799160f0e5957506d58254a693cbc231f`; bounded surviving-majority evidence inherited through management's ruling, not rerun or recertified here |

Public source versions and limits are recorded in section 12. Specification facts, this study's deductions, and hypothetical schedules are distinct evidence classes. No hypothetical trace below is an observed failure or a passing experiment. The new PR's commit and GitHub delivery comments supply the final report SHA; the report does not attempt to embed its own commit hash.

## 3. Threat envelope and the fact that must survive

Protected authority is not just epoch. Define a research tuple **H** containing protected-resource identity, predecessor/incarnation chain, decision index and parent head, owner/actor generation, admitted signer and verifier-policy floors, journal commitment, complete pending-set commitment and retirement/idempotency obligations. A valid signature over an old H can remain cryptographically valid while being unauthorized now. The terminal requirement is authenticated knowledge of **the latest legally committed H**, including every same-epoch OPEN and policy change.

The adversary can restore an older coherent majority of R together with W, application state, old credentials, and selected verifier/SQL/PG images. Messages may be delayed, duplicated, lost or reordered; partitions and crashes may occur at every persistence boundary. An old PostgreSQL transaction may already hold permission and later commit. E's own reset/restore/replacement privileges are examined rather than silently excluded. We do not assume simultaneous compromise of every possible physical mechanism can be solved; its limits must be explicit.

| Finite scenario | E1 witness-service condition and failure boundary | E2 protected-root condition and failure boundary |
|---|---|---|
| R majority + W + old signer rewound; E and guard stay current | Could compare current H and deny stale R, if E actually has terminal continuity and validated writes; not evidenced | Could deny mismatch against surviving protected H, if counter/head/journal binding and guard exist; not evidenced |
| E restored from its own old backup / reset by its controller | Ordinary service state can freshly authenticate an old H; fails unless a further surviving fact is concretely identified | Actual physical counter may survive specified software restore; virtualized/restored state does not inherit that guarantee. Reset, hierarchy and replacement envelope still requires qualification |
| R, verifier, SQL guard and old policy restored together | A witness nobody must consult protects nothing | A protected device nobody must consult protects nothing |
| Journal body/suffix missing, including same-epoch OPEN | Head mismatch can require denial; no reconstruction from digest | Larger counter/current digest can require denial; cannot synthesize missing OPEN bodies |
| Previously admitted old PG transaction still active/prepared | Preserve its exact hold; new owner excluded; current E alone cannot undo old permission | Same; hardware monotonicity does not undo a transaction |
| Split network, stale response or response delayed beyond revoke | Only current, correctly serialized admission may authorize; cached/old signer branch is insufficient | Device attestation must be tied to current admission and policy, not replayed as a timeless permit |
| E terminal fact/device lost, or all roots plus enrollment policy rewound | No evidenced continuity; unsupported, not an automatic fresh witness | No evidenced continuity; replacement device is not a clean resource history |

These are conditional failure envelopes, **not PASS results**. A finite independent trust assumption is legitimate only when the surviving artifact, actors allowed to alter it, and mandatory authentication/enforcement are named and qualified. Adding an unnamed second witness recursively is not qualification.

## 4. E1 — independent current-head witness

### 4.1 Concrete arrangement studied, not selected

The candidate is a separately administered state-machine service storing H and the authenticated operation journal, with independently controlled enrollment manifest, signer-policy floor and backups. It validates each transition against the previous head and all unresolved obligations. Authenticated current reads and compare-and-append decisions are required; a service that signs a caller's arbitrary larger sequence is rejected. Every admitted permission would require its current decision, and the independent deployment guard would prevent use of restored pre-E software.

The service's receipt would have to bind resource and E incarnation, prior and new decision indices/heads, policy and actor, operation/idempotency digest and journal/pending commitments. These are necessary semantic fields, not an approved wire format or cryptographic algorithm. A nonce can bind a reply to a request; it cannot tell whether a coherently restored service has forgotten later authority. Durable replication may preserve state under specified member failures, but independently replicated ordinary stores still need a terminal anti-rewind boundary under their own restore scope.

**Exact missing fact:** which non-restored artifact tells a verifier that E's current authenticated head is the latest, even after E administrators restore its entire service and signing state? No such artifact/custody mechanism is instantiated by this candidate. A separately surviving current quorum could define a *narrower survival assumption*, but it would repeat the H-style limitation at E rather than establish E's own catastrophe continuity. An independently pinned external high-watermark needs its own survival and update/enrollment story; otherwise it is an additional assumed oracle.

### 4.2 What related mechanisms do and do not establish

RFC 9162 supplies Merkle inclusion/consistency mechanisms and permits bounded CT publication delay; it does not define instantaneous latest CAC permission state [S1]. Our deduction: an old consistent checkpoint can prove a prefix while omitting a later OPEN. Auditors and gossip may expose equivocation later, but cannot substitute for mandatory synchronous admission before a local effect.

etcd documents strict serializability and durability for completed KV operations, with uncertainty when a client loses the reply [S6]. Our deduction: this is useful within its stated system envelope, not proof against restoring the whole authority or of atomicity with PostgreSQL. Increasing replicas or using a recovered logical cluster does not by itself authenticate the highest pre-catastrophe CAC head.

### 4.3 E1 feasibility outcome

Potential advantages are a natural place for a full journal, legal-transition validation, inspection and replicated service operation. Costs include independently governed infrastructure, online admission dependency, archive retention, independent incident and key-policy control, and long denial if latest state cannot be established. The primitive description supplies no verified terminal storage/custody mechanism and no G4 enforcement deployment. **Reject E1 as currently qualified**. Conditional stale-R detection is a research property under assumptions, not a supported recovery capability.

## 5. E2 — protected monotonic root plus complete journal

### 5.1 Concrete arrangement studied, not selected

The candidate combines an independently custodied physical monotonic state primitive, an authenticated ordered journal outside restored R, and a constrained transition authority. The proposed protected fact must bind H, not merely count requests. A current guard would verify the device/root incarnation, manifest and policy floor, journal ancestry and exact operation admission. Journal writers, protected-state updaters and guards need an explicit common legal transition rule. Unrestricted signing of supplied digests or counters is insufficient.

The published TPM 2.0 Library v185 is an **illustrative primitive specification**, not a chosen device, vendor, KMS/HSM or deployment. Part 1 §34.2.6.3 specifies counter increment semantics and same-Name deletion/redefinition protection: the first increment must exceed the previous lifetime value. Its orderly-counter rules also address unclean shutdown. Thus ordinary same-Name index deletion is **not** presented here as a counter rollback attack. NV extend has different persistence rules, including orderly-state behavior (§34.2.6.5); one must not transfer counter guarantees to every register [S3]. No hardware was obtained, commanded, reset, attested or audited.

NV certification describes an index Name, offset and contents [S4]. Our deduction: certification can identify measured bytes, but cannot prove that a caller-supplied head contains every CAC OPEN or that a PG transaction has ended. Part 3 documents privileged Clear/ClearControl interfaces [S5]; custody must address the actual hierarchy, firmware, reset and replacement mechanisms. We make no blanket assertion that every Clear resets every counter, or that disabling one command makes a platform administrator harmless.

### 5.2 Binding and lifecycle gaps

Two separate registers containing a counter and a hash do not automatically form one atomic authenticated CAC state. Incrementing a valid counter while binding an old or incomplete journal head yields a larger number with invalid authority semantics. A hash-chain register may help bind ancestry, but its persistence, authorized extension, body availability, policy enforcement and relation to the counter must be established for a particular primitive. No standard capability reviewed here establishes that whole compound transition on behalf of CAC.

A speculative conservative sequence could persist an exact journal candidate, bind it to protected state, then admit first use only after R and E evidence agrees. A crash between those steps must block new authority; it cannot cause fallback to an old counter or an empty pending set. This is a necessary design constraint, not a completed crash-consistent update protocol. Selection of storage attributes, head-to-index mapping, candidate recovery and sole authorized updater remains unresolved.

Key protection and state freshness are separate. Device replacement, hierarchy change, new attestation key, firmware change and verifier reenrollment must not permit a different root to declare an unchanged resource obligation-free. Destruction of the only surviving protected state can mean permanent denial. A software-emulated or snapshot-restored device is not evidence for the physical survival assumption. An independently current installation manifest must also survive R/PG/verifier rollback; otherwise old code can skip the device entirely.

### 5.3 E2 feasibility outcome

E2 provides a more concrete **primitive-level anti-decrement property** than E1's unspecified terminal service state. It still lacks qualified compound H persistence and transition validation, complete journal recovery, actual physical/reset custody and all-route enforcement. Hardware policy and application/outcome semantics have different trust boundaries. **Reject E2 as currently qualified**, without denying the documented counter property or claiming that a counter-only demonstration would answer CAC's question.

## 6. G1–G5 comparison and capability ladder

| Gate / retained P0 | E1 | E2 | Current disposition and evidence needed to change it |
|---|---|---|---|
| G1 / I-P0-01: terminal continuity | Independently named service, but terminal latest fact and own reset control missing | Real specified counter semantics; no qualified physical instance, compound H or lifecycle/custody | **DESIGN_BLOCKED**: identify finite surviving fact, actual reset/restore/rotation/enrollment authority and independent verifier. Service signatures or hardware labels alone fail |
| G2 / I-P0-02: full pending history | Could store bodies and checkpoints; independent completeness/availability not established | Protected commitment has no bodies; external journal completeness/retention not established | **DESIGN_BLOCKED**: authenticated prefix/suffix, pending set, retirement/tombstones and operation/incarnation/idempotency mapping. Missing data means deny |
| G3 / I-P0-03: cross-system ordering | Linearizable E is not an R/E/PG distributed commit | Protected update is not an R/E/PG distributed commit; torn counter/head additional cut | **DESIGN_BLOCKED**: implementable legal transition/ACK recovery contract still missing; section 8 gives falsification constraints only |
| G4 / I-P0-04: mandatory current routes | Independent service can be bypassed by restored old verifier or DB path | Independent device can be bypassed identically | **DESIGN_BLOCKED**: concrete external enforcement, trusted bootstrap/floor and complete incumbent route coverage; otherwise GLOBAL_FAIL_CLOSED_NOT_ESTABLISHED |
| G5 / I-P0-05: resource continuity | New service namespace/keys cannot reset obligations | New device/index/key cannot reset obligations | **DESIGN_BLOCKED**: resource-bound predecessor continuity across all incarnations; no automatic reenrollment after loss |

| Capability level | What would be required | What it does not imply | J status |
|---|---|---|---|
| DETECT_AND_DENY | Surviving authenticated current H + mandatory independent guard detects stale/missing state | Missing bodies cannot be recovered from a digest; even detection fails if guard rewinds | Conditional sketches only; no qualified E candidate; SECURITY_UNPROVEN / NOT_RUN |
| RECONSTRUCT_AND_CONSERVATIVELY_AUTHORIZE | All current pending bodies, ancestry, policy and tombstones authenticated to latest H; exact prior holds retained | Complete UNKNOWN history does not prove COMMIT or ABORT; no right to release orphan OPEN | DESIGN_BLOCKED / NOT_RUN |
| Release genuinely UNKNOWN old work | Positive exact outcome plus separately approved recovery design | Hard fence, time, human signature, status query or new root is not that proof | Lane3 P0 BLOCKED / NOT_RUN, outside J |

## 7. Physical, administrative and mandatory-enforcement boundaries

Separate accounts or personnel are useful controls, not a terminal antirollback proof. A common cloud root, SSO recovery administrator, backup decryption key, firmware operator or manifest signing authority can collapse purported independence. The following is a required custody inventory, **not an observed deployment**.

| Plane / actual power to identify | E1 requirement | E2 requirement | Consequence if shared, lost or restored |
|---|---|---|---|
| R/W/PG host and snapshot operator | Must not rewrite E's terminal state or current enrollment | Must not rewind protected physical state or reset its trust binding | R restore could become E restore; unsupported |
| E service/backup/recovery administrators | Separate storage, enrollment, current-policy and restore authority; explain who can import older service state | Journal operators separated from protected-state lifecycle authority; authenticated completeness even if bodies withheld | Restored head can freshly sign; missing journal forces denial |
| Physical device, platform hierarchy and firmware operator | Any hardware used by service needs its own lifecycle analysis | Exact platform/reset/firmware/hierarchy, deletion/redefinition and replacement powers documented | Claimed terminal property may not survive actual operation; no generic immunity assumed |
| Signing keys, PKI, manifest and policy-floor owners | Old keys and old policy cannot self-reenroll | Old device/attestation keys cannot self-reenroll | Fresh signatures under retired policy are still obsolete |
| Guard build/host/network admission controller | Independent current floor must cover restored issuers and DBs | Same, including permission to use/omit device | Old verifier can omit E; global denial not established |
| PG superuser, storage and outcome observer | Trusted/excluded powers explicit; outcome evidence independently current | Same; protected counter does not supervise PG superuser | RLS/ACL bypass or false closure possible |
| Incident responders and archive custodians | Cannot reset head/clear UNKNOWN by ceremony; independently evidenced isolation | Cannot replace device into clean history; preserve body/receipt retention | Operator approval is not a transaction outcome |

### G4 route inventory — concrete prerequisites, not implemented controls

For supported restore, a separately current controller would need to deny resource access **before** restored services can resume, authenticate admitted images/roles/policies, and cover old connections and already granted work. Network isolation alone does not prevent a local PG COMMIT or prove an old transaction aborted. A service's self-reported build or a restored DB policy table cannot establish its current admission. RATS distinguishes appraisal/policy and freshness; attestation is not by itself a CAC permission decision [S2].

| Route | Required independent control / state to verify | Present qualification |
|---|---|---|
| Issuer, old app, C-only/pre-E signer, cloned actor | Current external installation/actor/key-policy admission; old signer cannot mint usable new authority | No evidenced all-route installation; DESIGN_BLOCKED |
| SQL context entry and RLS authorization | Restored SQL cannot be the sole judge of whether E is required; current execution/privilege admission outside its rewind domain | No independent enforcement mechanism established |
| SECURITY DEFINER/private functions and direct DB roles | Complete function/build/ACL/RLS inventory and mandatory admission; trusted owner/superuser powers explicitly bounded | An old privileged function can bypass an added service check |
| PgBouncer clients, reused server connections and cached contexts | Current admission at exact transaction first use, DB incarnation/operation binding; track incumbent transactions through revoke | Rejecting new clients or NOLOGIN alone is insufficient |
| Existing active/prepared PG transactions | Account prior legitimate grants and holds; deny successor while effects remain possible; verify isolation without inventing outcome | Cancellation/session loss is not a durable exact ABORT receipt |
| Alternate listener, local socket, maintenance/admin path | Host/database privilege and resource-path coverage, independently enforced before restart | Same-host loopback/admin bypass cannot be hidden by pool-only tests |
| Old verifier, bootstrap, manifest/key-policy enrollment | Current external trust floor and admission; cannot accept an old self-signed manifest or reenroll a clone | Joint restore remains GLOBAL_FAIL_CLOSED_NOT_ESTABLISHED |

No concrete, audited mechanism covering all these paths is supplied by either candidate. Both therefore fail G4 now. Even if later isolation is evidenced, previously admitted work remains accounted for; `ISOLATION_REQUESTED` is not `VERIFIED_QUARANTINED`, and verified quarantine is not a positive local outcome.

## 8. Research state model and linearization constraints

This section gives a **non-executable falsification model**, not a chosen protocol, API, SQL contract, lease, timeout, algorithm or 2PC design. It exposes missing atomicity; it does not prove realizability. PostgreSQL's documented prepared-transaction support is intended for an external transaction manager [S7]; choosing it would still require authority/outcome/custody semantics and is not done here.

Represent an exact operation by resource, predecessor chain, actor/root/DB incarnation, operation/idempotency digest and local transaction binding. States under study are UNADMITTED, OPEN_RECORDED, FIRST_USE_GRANTED, OUTCOME_KNOWN and CLOSED; **OPEN_UNKNOWN retains its hold**. A separate REVOKE_INTENT orders owner transitions. R-only/E-only candidate records are not permission. A returned message is not a linearization point merely because it was signed.

Necessary invariants:

1. **Before usable first permission:** exact OPEN is durable in R and in E's authenticated complete history. Durable absence of permission before this point is required; no local effect may precede it. An unresolved candidate cannot be retried as a different operation to escape a hold.
2. **One authorization order:** FIRST_USE_GRANTED must have one canonical serialization with REVOKE_INTENT. If grant precedes revoke, exact old work may continue but its durable hold blocks successor readiness. If revoke precedes grant, the grant is denied. Staging in two independent roots is not this serialization; the binding protocol remains DESIGN_BLOCKED.
3. **First-use binding:** a delayed reply is usable only for its admitted exact transaction under current policy. It cannot grant another transaction or resurrect an operation that never reached canonical first use. Transport freshness and signature validity do not supply the missing order.
4. **Outcome before close:** hold removal requires positive durable COMMIT/ABORT evidence for the exact DB incarnation and operation, trusted under current policy, followed by authoritative close publication in R/E. A close at only one root cannot establish successor READY. Observer rollback or ambiguous local ACK prevents inference.
5. **Ambiguity preserves obligations:** lost E/R/PG ACK, unavailable body or uncertain prefix blocks new authority and preserves every possible hold. Querying the original idempotency key may discover an **already canonical** OPEN/grant/CLOSED; it cannot manufacture an outcome. A genuinely UNKNOWN operation stays BLOCKED throughout this study.
6. **No successor overlap:** SUCCESSOR_READY requires current concordant authority and a complete authenticated account showing no unresolved prior permission that may still commit. A fully known CLOSED record can resolve a lost reply; missing evidence or truly UNKNOWN cannot.
7. **Identity continuity:** all H updates preserve protected-resource predecessor obligations. New root, actor, journal, device or DB names cannot produce an empty safety history for the same resource.

The ideal linearization obligation is therefore an E-bound, legally validated canonical grant ordered with revoke and carrying an already durable exact OPEN, with R concordance before use. This report does **not** specify how two roots make that grant crash-recoverable, how a physical primitive validates it, or how all PG paths enforce it. Those missing mechanisms are a G3 blocker, not delegated implementation details. E/R disagreement cannot be repaired by choosing whichever copy permits progress.

### Hypothetical adversarial cuts — all NOT_RUN

These traces are counterexamples to tempting weaker designs, not reports of new observed security failures. “Deny” below means the required decision **if independently current mandatory enforcement exists**; otherwise G4 fails and global denial is unestablished.

| Cut | Hypothetical schedule / weaker design falsified | Required conservative result and missing evidence |
|---|---|---|
| J-C01 | E1 backup rewinds head 12→9 with old keys; nonce is fresh; R also returns 9 | Fresh signature is insufficient. Reject qualification without terminal latest fact; do not label this detected |
| J-C02 | Epoch unchanged; OPEN q added at head 13; restored journal ends at 12; compare only epoch | Deny, never infer empty set. Need full operation-sensitive head and completeness evidence |
| J-C03 | R persists OPEN; crash before E records it; issuer treats R ACK as permit | No usable permission. Divergence/candidate state blocks; no R-only fallback |
| J-C04 | E durably records OPEN/grant; ACK lost; caller retries with new operation ID | Keep original hold; authenticated exact-id status only. New ID cannot erase possible prior permission |
| J-C05 | E2 counter advances; crash before associated head/body binding; boot reads larger counter and old journal | No permission. Counter and old digest cannot be accepted as compound current H |
| J-C06 | Authorized raw primitive caller increments counter and certifies stale journal digest | Numerically higher state is not a legal transition. Need constrained semantic updater and prior-head/pending validation |
| J-C07 | Grant reply delayed; REVOKE_INTENT occurs; reply arrives and starts another PG transaction | Deny substituted/unadmitted first use. Legitimate pre-revoke exact grant retains its hold and blocks successor |
| J-C08 | Old grant executes PG COMMIT; ACK lost; client disconnects; timeout closes OPEN | Preserve UNKNOWN hold. Neither timeout nor disappearance proves ABORT; successor BLOCKED |
| J-C09 | E publishes CLOSED before exact PG durable outcome; successor READY; old transaction later commits | Invalid ordering; cannot publish usable close/READY on intention. Positive outcome and R/E close evidence required |
| J-C10 | Partition: old E signer/cache serves earlier head/policy; another side admits new owner | No stale/cached admission. Current serialization/policy plus old-work holds required; unresolved split blocks new authority |
| J-C11 | E stays current; old verifier+SQL image restored; incumbent PgBouncer transaction uses C-only function | E comparison on new path is irrelevant. G4 failure; GLOBAL_FAIL_CLOSED_NOT_ESTABLISHED until actual mandatory coverage proven |
| J-C12 | Journal prefix/header restored without an OPEN body or retirement/tombstone suffix | Detection may work; reconstruction cannot. Missing authenticated suffix/body blocks, not an empty pending set |
| J-C13 | Root/device lost; operator enrolls new namespace/actor/key against unchanged resource | No fresh genesis/READY. Predecessor obligations remain; total loss may mean indefinite exclusion |
| J-C14 | Both roots have canonical exact CLOSED with positive outcome; final response alone lost | Current authenticated lookup may recover that existing record. It cannot close a genuinely UNKNOWN operation; if evidence unavailable retain hold |

## 9. Operational feasibility, cost and availability

No prices, capacity, SLA, RPO/RTO, latency, throughput or device endurance measurements were collected. The comparison concerns required resources and failure modes, not a procurement estimate. Physical antirollback custody cannot be established from published specifications or CI alone.

| Dimension | Option A: retain unsupported catastrophe scope | E1 service family | E2 protected-root + journal family |
|---|---|---|---|
| New infrastructure | No E added; existing current-guard requirement still unresolved | Independent current-head service, replicas/storage, full journal, enrollment/policy control | Protected-state lifecycle, qualified updater/guard, journal/archive and enrollment/policy control |
| Independence | Does not claim to solve restored-majority authority | Service administrators, backup/reset and trust-floor custody must survive R; “another account” is not sufficient | Physical/platform/firmware and key/reset custody must be separated from R; journal and guard also independent |
| Request and persistence burden | No new E request path; no new continuity benefit | Online current admission and durable state transitions; journal retention and pending growth | Protected updates/attestation plus full journal operations; device persistence/endurance and serialization limits need measurement |
| Availability | Catastrophe can cause unsupported/indefinite outage; no automatic recovery | E partition or missing latest state blocks new authority; replicas improve only stated failure envelope | Device loss/replacement or binding ambiguity can block indefinitely; hardware replication is another continuity problem |
| Disaster recovery | No unverified R-majority re-genesis | E's own recovery remains the central unsolved requirement | Physical fact can outlive some software restores, but loss/reset/replacement must not manufacture fresh history |
| Operator burden | Incident isolation and honest unsupported declaration | Separate custody, guarded restore and enrollment, body retention and outcome-observer policy | All E1 journal/policy duties plus device inventory, physical custody, lifecycle and replacement controls |
| Economic evidence missing | Cost of prolonged denial and incident response | Independent operations, storage/retention, round trips, audit and recovery cost | Physical operations, protected-write characteristics, spares/replacement, archive and online guard cost |

E1 may be easier to query and replicate than a physical root, but that convenience does not solve its terminal rollback boundary. E2 offers a specified primitive surviving some nonphysical rewind scenarios, but introduces lifecycle and binding complexity and still needs a service/journal and mandatory guards. Both may retain UNKNOWN indefinitely, so improved detection is not availability recovery. High update rates and persistence configuration require actual device-specific study; no numerical sizing is inferred from a generic hardware label.

Incident handling must distinguish intact restart, inaccessible root and responsive coherent rewind. A current read from a rewound root is not a detection signal. Required future evidence includes independent isolation receipts for every route, exact outcome-observer custody, and authoritative body retrieval. Proposed monitors may request isolation; they do not prove it occurred. PG prepared/active work must remain attributed to its old incarnation through all operations.

## 10. Findings and proposed architecture decisions

| ID / severity | Research finding, trust assumption and proof status | Proposed disposition / corrective requirement |
|---|---|---|
| I-P0-01 / G1 | E1 terminal own continuity unspecified. E2 primitive counter property documented, but compound authority/custody unqualified. Assumes surviving independently authenticated latest fact; SECURITY_UNPROVEN / NOT_RUN | **DESIGN_BLOCKED**. Require actual terminal state/lifecycle and bounded reset/replacement/admission story before detailed protocol or experiment request |
| I-P0-02 / G2 | Neither family supplies complete authenticated pending history and available bodies. Assumes durable independent journal; NOT_RUN | **DESIGN_BLOCKED**. Specify completeness, checkpoints, same-epoch suffixes, retention, idempotency and retirement; detection-only must remain deny-only |
| I-P0-03 / G3 | Separate durable roots and PG have no implemented or fully designed common grant/close order. Assumes exact trusted local outcomes; NOT_RUN | **DESIGN_BLOCKED**. Legal transition model, lost-ACK semantics and every cut must be independently challenged; no premature READY |
| I-P0-04 / G4 | Neither current root nor hardware can compel restored old SQL/verifier paths to consult it. Assumes independent mandatory admission and bounded privileged operators; NOT_RUN | **DESIGN_BLOCKED / GLOBAL_FAIL_CLOSED_NOT_ESTABLISHED**. Concrete independent deployment/custody evidence and exhaustive route coverage required; bypass stops qualification |
| I-P0-05 / G5 | New identities could conceal same-resource obligations without external predecessor continuity. Assumes immutable resource attribution; NOT_RUN | **DESIGN_BLOCKED**. No root/device/namespace/actor replacement into clean READY; missing history keeps resource blocked |
| I-P1-01 | Silent rewind incident trigger and verified quarantine unavailable; assumes current independent observer/controller; NOT_RUN | Keep SECURITY_UNPROVEN. Separate request, receipt and actual all-route isolation, including incumbent effects |
| I-P1-02 | PG observer/admin rollback can falsify exact outcome/closure assumptions; no device can infer COMMIT from head; NOT_RUN | Keep SECURITY_UNPROVEN. Specify exact operation/DB incarnation/effect receipt and privileged custody; no generic session-liveness shortcut |
| I-P1-03 | Independent service or physical-root operations introduce online dependency, retention and potentially indefinite denial; no cost/capacity evidence | Keep unpriced / NOT_RUN. Resource/custody model before numerical sizing; do not infer availability from redundancy alone |
| I-P2-01 | Public primitive specifications, design requirements and previous bounded test evidence have different provenance | Preserve immutable identities and explicit status labels; no substitution of DESIGN_SPECIFIED or counter property for SECURITY_PROVEN |

Proposed decision record changes, **not approved ADR/APR edits**:

- Record J's negative qualification verdict and retain Option A's conditional quarantine wording. Keep E1/E2 as rejected-current-qualification research sketches, not committed recovery architecture or a technology decision.
- Add the explicit distinction between a specified anti-decrement primitive, an authenticated legal current head, a complete available journal, and mandatory current enforcement. Qualification requires the compound system; each layer can fail independently.
- Preserve a resource-bound predecessor rule through service/device/key/namespace replacement. Do not add an exception for human approval, hard fence or UNKNOWN timeout.
- Require a separate adversarial read-only review of this study, then a new management vote for **any** further implementation or active custody investigation. A documentation refinement may narrow assumptions; it cannot close the P0s by wording.

## 11. Smallest future falsification proposal — NOT_RUN, not authorized

The first useful next step is documentary, not another assumed oracle: request a concrete candidate's terminal-state lifecycle and mandatory-route custody dossier. It must identify exactly who can restore/reset/replace each state and policy, the actual physical or independently surviving fact, its legal updater, journal binding, and independent guard coverage. Apply **G1 and G4 first**. If no finite credible boundary exists, stop and keep Option A; a new mock head service would only repeat S0-09F's assumed-root premise.

Only if a later independent review finds that dossier credible and management separately authorizes an experiment, the smallest **future** proof would try to falsify one narrow claim: *an old R view cannot obtain new permission for the same resource while the named terminal E fact and mandatory guard survive*. It would need a real qualified primitive and controls, not an oracle that assumes the desired property. Proposed evidence boundaries:

| Future step | Required evidence / rejection condition | Present status |
|---|---|---|
| Dossier and model challenge | Named finite reset/custody envelope; all-route admission; independently review C01..C14 and legal transition model; fail early on unqualified E/guard | Proposed further documentation; NOT_RUN, no acceptance |
| Exact operation baseline | Durable OPEN body and R/E heads, exact transaction/actor/DB mapping, ordered first-use/revoke/known-outcome/close receipts | NOT_RUN; would need separate execution authorization |
| Minimal restoration and cut controls | Old R versus surviving terminal E, body omission, lost ACK, torn head binding and delayed grant; preserve all UNKNOWN; never test orphan clearing under this proposal | NOT_RUN; actual custody and physical properties cannot be replaced by mock fixtures |
| Independent sensitivity controls | Separately remove current-head check, body-completeness check and old-route admission in isolated synthetic fixtures; expected RED per control, byte-identical restoration and GREEN baseline; never weaken production/security assertions to pass | Proposal only / NOT_RUN; not executed by J |
| Final adversarial assessment | Compare observed permissions, durable bodies and actual route effects, not just endpoint status; report any old new-permission as FAIL_SECURITY; ambiguous evidence BLOCKED | NOT_RUN; no security acceptance or deployment inference |

The proposal excludes whole-E recovery, majority-R recovery supported in Production, physical clone security and Lane3. It cannot certify E against its own total-loss/reset envelope unless that separately authorized investigation actually covers it. No fixture, experiment, CI run, workflow or code for this plan has been created. Existing test results are not reclassified as the plan's evidence.

## 12. Public source ledger and limits

Sources were read on 2026-11-07. Links identify the retrieved public specification/version, not a selected provider. The statements attributed to each source are limited to documented primitive behavior. CAC requirements, failure schedules and rejection judgments above are this study's deductions.

| Ref | Source and inspected scope | What it supports / does not support |
|---|---|---|
| S1 | [RFC 9162, Certificate Transparency v2](https://www.rfc-editor.org/rfc/rfc9162.html), December 2021, Experimental; §2.1.4 and STH/MMD rules | Append-only consistency and CT publication/freshness model; not an online CAC current-authority service or transaction journal |
| S2 | [RFC 9334, RATS Architecture](https://www.rfc-editor.org/rfc/rfc9334.html), January 2023, Informational; appraisal/policy and §10 freshness | Attestation's trust/policy/freshness separation; not mandatory enforcement of old SQL or authorization across restored roots |
| S3 | [TCG TPM 2.0 Library, published v185](https://trustedcomputinggroup.org/resources/documents/tpm-library-specification), 2026-03-12; [Part 1 Architecture](https://medias.cdn.trustedcomputinggroup.org/production/Trusted_Platform_Module_2_0_Library_Part_1_Architecture_Version_185_pub_2a3392dc49.pdf), §34.2.6.3 and §34.2.6.5, printed pp.248–250 | Counter lifecycle/monotonic rules and distinct NV-extend semantics; not CAC journal binding or audited physical hardware. Published version used, not the earlier v185 RC4 draft |
| S4 | [TCG TPM 2.0 Part 2 Structures, v185](https://medias.cdn.trustedcomputinggroup.org/production/Trusted_Platform_Module_2_0_Library_Part_2_Structures_Version_185_pub_c0a962a931.pdf), §10.11.8, TPMS_NV_CERTIFY_INFO, printed p.160 | Certification structure identifies NV contents; not proof that application transitions or local outcomes are correct |
| S5 | [TCG TPM 2.0 Part 3 Commands, v185](https://medias.cdn.trustedcomputinggroup.org/production/Trusted_Platform_Module_2_0_Library_Part_3_Commands_Version_185_pub_87a5c10230.pdf), §24.6–24.7 | Privileged lifecycle/control interfaces require explicit custody analysis; not evidence of a purchased/configured device or absolute reset immunity |
| S6 | [etcd v3.6 API guarantees](https://etcd.io/docs/v3.6/learning/api_guarantees/) | KV operation guarantees and uncertain client reply; no cross-PostgreSQL atomicity or whole-authority antirollback guarantee |
| S7 | [PostgreSQL 17 Two-Phase Transactions](https://www.postgresql.org/docs/17/two-phase.html) | Prepared transactions/external-manager facility; not a selected CAC protocol or proof of R/E/PG safety |

## 13. Evidence/status handoff and unchanged gates

| Item | Status after J | Evidence boundary |
|---|---|---|
| Two-family feasibility, custody/G1–G5 comparison and hypothetical cut matrix | Documentation delivered; negative qualification recommendation | Public specifications + commit-pinned governance; no empirical PASS |
| All five E P0 gates | DESIGN_BLOCKED | No terminal compound E/current-guard implementation or verified custody |
| E1/E2 real independence, own restore/rotation, journal/PG ordering | SECURITY_UNPROVEN / NOT_RUN | No deployment, hardware, keys, accounts or experiments |
| S0-09D original C-only rollback | **FAIL_SECURITY**, unchanged | Historical actual failure, not rerun or silently fixed by adding E language |
| S0-09H | Bounded surviving, non-restored real 3-of-5 majority evidence only | Management records 169 inherited + 51 H distinct DB/security methods across separate suites, plus 2 artifact-only methods and five mutation controls. Not E or majority-catastrophe proof; not rerun here |
| Actual root policy retirement; literal stale Raft snapshot/WAL import | **NOT_RUN** | Neither inherited success nor this research closes these gaps |
| Lane3 / orphan OPEN_UNKNOWN release | **P0 BLOCKED / NOT_RUN** | No timeout, operator, fence, new identity or status-lookup exception |
| Root-majority catastrophe / simultaneous old verifier / physical clone | UNSUPPORTED or SECURITY_UNPROVEN / NOT_RUN | GLOBAL_FAIL_CLOSED_NOT_ESTABLISHED when mandatory current enforcement is absent |
| New security tests, CI, PoC, code/SQL/migrations/workflows/infrastructure | **NOT_RUN / NOT_CHANGED** | Only this Markdown deliverable; no run dispatch or inherited experiment repetition |

All prior PRs remain Draft/unmerged; none is modified by this report. Issue #36 receives delivery, not automatic closure. Architecture #33/#28/#23 and Gate #9 stay **OPEN**; SOURCE-001 #1 / GATE-SOURCE stay **BLOCKED**. No APR-033..036 change, source recovery claim, accepted baseline, Sprint0 completion, Production, identity/MFA/onboarding, vendor, key-management or security-protocol approval is issued.

**Vote for Astra Management: `NO_CREDIBLE_E_CANDIDATE_KEEP_A`.** Seek an independent adversarial read-only assessment of this bounded negative qualification and any concrete new terminal/custody evidence. Every active next step requires a separate management decision. No result here authorizes implementation, root catastrophe recovery or release of UNKNOWN work.
