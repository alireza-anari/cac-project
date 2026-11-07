# S0-09G R1 — independent security design delta review

**Date:** 2026-11-06 (Asia/Tehran). **Role:** Astra Security Architecture Reviewer / Work. **Audience:** Astra Management. **Tracking:** [Issue28](https://github.com/alireza-anari/cac-project/issues/28), parent [Issue23](https://github.com/alireza-anari/cac-project/issues/23).

**Vote: READY_TO_REQUEST_BOUNDED_QUORUM_SURVIVAL_POC — Q_SURVIVAL_SCOPE_ONLY.** R1 is sufficiently explicit at the contract level to request consideration of a narrowly bounded W/minority-R restore experiment while a current, admitted, non-restored R majority and mandatory independent verifier enforcement survive. No further contract redesign is required for **that request alone**. This is not readiness to implement, general Lane2/root-recovery acceptance, or proof that the deployment premises can be enforced. **NO_EXECUTION_AUTHORIZATION / SECURITY_UNPROVEN / PROTOCOL_PROPOSED.**

This updates the accepted R0 finding disposition only for the narrowed boundary. R0's broader real-root own-majority rollback question is not solved, reclassified as safe, or reopened as a new review. Any request that promises automatic majority/root rollback recovery, copied-root/old-verifier safety without surviving enforcement, or orphan clearing remains **DESIGN_BLOCKED** under this review.

## 1. Verified inputs and review method

| Input | Pinned identity |
|---|---|
| Live management main, initial review | `3dcd1c0896d05be2097ad7aa64f774a66e816043` |
| [Primary R1](https://github.com/alireza-anari/cac-project/blob/3dcd1c0896d05be2097ad7aa64f774a66e816043/docs/architecture/S0_09G_TARGETED_ROOT_REFINEMENT_R1.md) | Git blob `4bf8db106456bfa5d58028d083a69d6c0ab64110` |
| R1 content SHA256 | `2ad16911a4848d398a789799bad327f83355699961c828ee5e24a6524806c0d5` |
| R1 last modifying commit | `c77f994a8049f2ff1cba040814c60a03a4651cb4`; later main commits record status/provenance |
| Accepted [R0 review, Draft29](https://github.com/alireza-anari/cac-project/blob/e63b16a0916aa6a43d5a36a20027dab20b506464/docs/security/S0_09G_ROOT_DESIGN_READ_ONLY_REVIEW.md) | `e63b16a0916aa6a43d5a36a20027dab20b506464`, still Draft/open/unmerged |
| Unchanged parent R0 | Content SHA256 `6ca7ce3b38a457642bfd4c0a563ab8e20eaab2abfde2c053340c5594f6e7ac59` |

Live GitHub main, R1 raw content, Issue28 and its management acceptance/R1 comment, and prior PR heads were read. Remote R1 content matches the checkout byte-for-byte. References to R1 lines use its pinned 108-line version. The nine accepted findings (five P0, three P1, one P2) are the baseline. This report evaluates their delta; it does not redesign R or repeat D/F.

Independence is from management R1 authorship. Prior CAC review/implementation involvement does not constitute external certification, an independent infrastructure operator, formal verification or a hardware evaluation. No code, SQL, migration, workflow or test is changed or executed; no runtime suite, dependency installation, experiment or manual CI dispatch is performed. Only this Markdown review is added in a separate Draft PR against main. Read-only repository/hash/diff checks are documentation verification, not security tests or a runtime PASS.

### Status vocabulary

- **DESIGN_SPECIFIED:** the requirement and supported boundary are concrete enough to scope a permission request. It is not a security result.
- **SECURITY_UNPROVEN:** the stated mechanism, deployment premise or enforcement property still needs implementation/operational evidence; no empirical closure is claimed.
- **DESIGN_BLOCKED:** the stated broader claim conflicts with the narrowed boundary or still lacks a permissible supporting contract. It cannot be inferred from the request-readiness vote.
- **NOT_RUN:** the corresponding real-R experiment has not been executed in this review. Prior D/F results do not change that status.

Design disposition, security assurance and execution status are recorded separately below; one must not substitute for another.

## 2. Five accepted P0 findings — R1 delta and disposition

| Accepted finding | R1 delta | Design disposition for Q-survival request | Security / execution |
|---|---|---|---|
| **G-P0-01: terminal surviving continuity fact** | Lines15–32 replace a generic irreversible-root placeholder with five admitted voters, majority durable log commit/current read, at least three current non-restored survivors, controlled membership continuity and learner-only restore. Root-majority/custody loss has no automatic recovery | **DESIGN_SPECIFIED**, only for the explicit surviving-state fault envelope. It does not establish absolute R nonrollbackability | **SECURITY_UNPROVEN**; real quorum durability, correct protocol, surviving-history/admission and independent custody not demonstrated. **NOT_RUN** |
| **G-P0-02: bootstrap/signer/verifier enforcement** | Lines36–44 define independent manifest/enrollment, current majority-backed policy, ordered signer retirement, non-self-admission, all-path pre-access network/DB quarantine and unsupported clones | **DESIGN_SPECIFIED** as a mandatory acceptance/stop condition. It is not a claim that a verifier running elsewhere automatically fences old endpoints | **SECURITY_UNPROVEN**; actual direct issuer/SQL/RLS/pool exclusion, trust-policy continuity and root-member admission require evidence. **NOT_RUN** |
| **G-P0-03: atomic head/OPEN/journal** | Lines48–59 make the majority-committed state-machine log the complete authoritative journal. Head/owner/policy/OPEN update at one committed index; permit follows durable commit, complete checkpoint plus contiguous replay, idempotent ACK handling | **DESIGN_SPECIFIED**; no scalar-root/W-only-journal success path remains | **SECURITY_UNPROVEN**; storage acknowledgment ordering, deterministic application, checkpoint completeness, evidence validation and crash behavior need proof. **NOT_RUN** |
| **G-P0-04: first-use/revoke order** | Lines63–77 introduce durable transaction-bound FIRST_USE_GRANTED in the same order as REVOKE_INTENT; earlier grants retain holds, later grants deny. No instantaneous physical cancellation promise | **DESIGN_SPECIFIED**; the R0 logical-order versus physical-time ambiguity is resolved for this bounded invariant | **SECURITY_UNPROVEN**; actual local binding, delayed delivery, grant retries, session reuse and no successor/old-commit overlap need proof. **NOT_RUN** |
| **G-P0-05: hard fence versus UNKNOWN** | Lines81–85 explicitly supersede the R0 alternative: positive durable CLOSE for every old operation before successor readiness; UNKNOWN/fenced-unresolved stays blocked despite physical isolation, elapsed time or operator approval | **DESIGN_SPECIFIED**; no hard-fence-only or Lane2 orphan-release exception | **SECURITY_UNPROVEN**; the implementation must preserve this exclusion through replay, restart, policy/membership changes and lost ACK. **NOT_RUN** |

**No P0 is empirically discharged.** The change is from missing/ambiguous contract to a reviewable restricted contract; it is not a transition to security acceptance. The accepted historical R0 findings remain valid for broader restore claims outside the revised envelope.

## 3. G-P0-01: what 3-of-5 does and does not mean

For a fixed five-member configuration, two sets of three intersect. That arithmetic alone does not authenticate history or provide consensus safety. Q additionally requires correct durable replication/election rules, current term and committed configuration, protected persistent member state and current reads. Relevant consensus literature separates log safety, membership transitions and client freshness [T1]; it is not enough for three endpoints to repeat the same owner or possess copied keys.

R1's surviving fact is **existing admitted committed history**, not the number three, a newly created quorum or a signature. A supported W/minority restore must preserve that fact throughout. Observing three healthy responses does not itself prove that their disks, membership or custody were never rolled back. A future request must identify which members/configuration/history remain intact and what actions the restore controller can perform. Where a selected protocol has more permissive fault tolerance, this review does not enlarge R1 to that boundary.

Restoring one or two members is permitted **only through the quarantined non-voting learner/admission path**. Directly replacing a live voter's persistent term/vote/log with an old snapshot and letting the same identity vote is not the stated experiment. It can violate the persistent-state premises of a crash-fault consensus protocol. Membership change must follow the chosen protocol's safe committed configuration transition; local learner flags or reusing an old voter credential are not sufficient. R1 specifies this obligation; its enforceability is unproved. Non-voting catch-up and checked promotion are established interface concepts [T2], not certification of an unspecified R.

### Majority loss/rollback must stay outside the safety claim

R1 lines17/25/27 must be read with lines15/24: **any loss or rewind that invalidates the required current non-restored majority is outside Q**, whether or not the verifier software itself was rolled back. Do not reduce this exclusion to only the case where both majority and verifier were restored together.

There is an important residual P0 distinction:

- An unavailable quorum or independently detected custody/history discontinuity can cause a current mandatory guard to deny.
- A **responsive but rewound majority** with still-accepted keys/configuration may produce a consistent stale history and fresh replies. A current guard with no independently retained newer fact is not thereby a majority-rollback detector. R1 has not supplied such a detector, and this vote does not infer one.

Thus line27's deny rule is a required response when continuity is unavailable/unverified; it is **not evidence that every forbidden majority rollback is automatically recognized**. A scoped request must retain this interpretation explicitly. Catastrophic majority recovery, fresh genesis posing as continuity and automatic denial detection for a fully rewound responsive root remain DESIGN_BLOCKED/SECURITY_UNPROVEN outside the proposed experiment. Existing snapshot-recovery guidance illustrates why restored revisions/new logical identities are not an independent latest-history witness [T3].

This boundary is honest enough for the Q-survival request because the majority is expressly required to remain non-restored. It does not solve R0's universal own-root rollback problem or justify a Production anti-rollback-root label.

## 4. G-P0-02: independent verifier is an enforcement obligation, not a proven capability

R1 improves the contract materially: an externally governed manifest plus enforced network/DB authority admission is required **before** old code can issue or query; minimum guard/policy and signer retirement are committed, and self-admission is forbidden. The answer to whether it can **actually** block all legacy routes is still **SECURITY_UNPROVEN**. Neither the document nor the previous F evidence supplies that real deployment proof.

For a permission request, the trusted boundary must enumerate direct issuer calls, direct SQL/RLS, established sessions, PgBouncer client/server backends, old endpoint addresses and any allowed local route. It must identify the independent authority that measures/adopts the manifest and disables/drains old access. Every route must either pass through that mandatory boundary or be explicitly unavailable in the scoped experiment. READY=false or a new verifier's refusal is not enough while another old endpoint can still authorize.

The same requirement applies to restored R members: current application policy is not by itself root-member voting/admission enforcement. Root, member, verifier and actor identities are distinct. Credential retirement, current configuration and reenrollment must prevent a quarantined minority from serving or voting as the current namespace before resynchronization.

R1 deliberately excludes SQL superuser/root bypass, simultaneous loss of every trusted boundary and unsupported copied physical actor/root identities. This is not evidence that ordinary RLS constrains those privileged actors. If the proposed environment cannot enforce the declared old-route quarantine outside W/A/B/C restore, that mode must STOP/remain unsupported; it cannot be excused by the request-readiness vote.

Signer retirement is now ordered for new authorization. Historical verification/replay using an old public key must remain anchored to the current authenticated prefix/policy; retaining such a key for history cannot make it eligible to mint current authority. The exact policy representation and receiver enforcement remain proof obligations, not a selected cryptographic contract.

## 5. G-P0-03..05: atomic root history and local outcome boundary

**One authoritative commit.** R1 no longer proposes a counter in R with the meaningful OPEN payload solely in W. The committed R log is both the head/owner/policy state and the full operation journal. A deterministic transition at one committed index is a sufficient contract-level answer to the previous split-commit gap. W is a replayed consumer/cache; it cannot make an uncertain root update authoritative by updating its own state first.

That is not evidence that a particular implementation acknowledges only durable writes or applies/checkpoints them correctly. Commit-before-permit, exact prior-head/configuration, idempotency/tombstones, complete UNKNOWN membership and authenticated checkpoint/suffix replay all need actual fault evidence. A close-evidence reference is not itself positive outcome evidence: an approved observer/validator must validate the exact operation/DB incarnation/transaction outcome before CLOSE commits. Its trust scope and prepared-transaction policy must be stated in the future request. R1 does not authorize implementing a new orphan resolver to fill this gap.

**First use and revoke.** For the request predicate, FIRST_USE_GRANTED is the logical R authorization point, not the physical arrival time of a reply or instantaneous cancellation of local PostgreSQL work. If grant G precedes revoke V, the exact already-identified local transaction remains tracked even if its response/use is delayed; it may still commit while B remains NOT_READY. If V precedes G, G must deny. A delayed grant cannot be transferred into a different transaction/actor. Abandoning the original transaction or losing its response does not erase its hold. Repeated status lookup must not create another grant or unrelated local effect.

**Successor exclusion.** A first-use status check alone is still insufficient. The unresolved hold must stay durably present until positively known local outcome and committed CLOSE. All earlier operations must satisfy R1's close rule before successor READY/live permission. A reserved next epoch is not permission. Root outage, missing replay or an ambiguous local/CLOSE ACK cannot open a gap in this rule.

**Hard fence.** R1 expressly removes the R0 shortcut. OPEN_UNKNOWN or FENCED_UNRESOLVED remains BLOCKED after actor shutdown, credential retirement, session loss, timeout or operator approval. Lane2 has no UNKNOWN-to-CLOSED recovery exception. Looking up a CLOSE that was already authoritatively committed for the same known outcome is idempotent observation; appending a new resolution for an orphan is not, and remains Lane3. These are clear contract distinctions; none is experimentally verified here.

## 6. Three P1 findings and one P2 — delta disposition

| Accepted finding | R1 coverage | Disposition and remaining obligation |
|---|---|---|
| **G-P1-01: custody/failure/cost** | Lines25–32/89 identify independent voting/backup/enrollment/replacement authority, shared parent controls, capacity/latency/journal/retention and incident costs; Q and B kept distinct but potentially complementary | **DESIGN_SPECIFIED** as required scope information; actual role/authority matrix, separation and cost/capacity remain **SECURITY_UNPROVEN** / **NOT_RUN**. The eventual request must identify its real custody/failure scope, not claim five processes are five independent administrators |
| **G-P1-02: live quarantine/replay enforcement** | Lines36–44/57/90 explicitly include old direct SQL/issuer, RLS and pooled sessions, independent policy and complete replay | **DESIGN_SPECIFIED**; **SECURITY_UNPROVEN**, **NOT_RUN**. Actual old-route access after supposed quarantine is a failure, not a tolerated limitation of a supported mode |
| **G-P1-03: falsifiable positives/RED/GREEN** | Lines91/96–101 require admitted valid positives, actual faults versus one-control weakening, intended assertion failure, exact restoration and final-head evidence/review | **DESIGN_SPECIFIED**; all actual execution **NOT_RUN**. Missing tickets, invalid args, unadmitted contenders, error-only RED or a forced continuity-loss flag cannot establish root safety |
| **G-P2-01: claim/provenance versioning** | Lines92/108 separate contracts from proof, pin members/config/software/custody/run IDs and preserve distinct prior counts/failure | **DESIGN_SPECIFIED**. Preserve this ledger in a future request/result. No product, wire/key format, TTL or APR is ratified; no new security evidence is created by this review |

### A/Q versus B — delta to the accepted comparison

| Dimension | R1 Q, within surviving-majority envelope | R1 alternative B |
|---|---|---|
| Root continuity claim | Continuous authenticated committed history survives in the admitted majority; no total-majority restore claim | Protected sequence **and state digest** plus complete log could address a different restore envelope if a real capability and current verifier exist |
| Evidence now available | Design contract only; no actual R quorum experiment | No physical primitive selected/evaluated; no real B proof |
| Independence | Non-restored voters and verifier/manifest authority must be outside W/A/B/C restore control; common parent administrators remain an explicit risk | Reset/replacement/firmware/key/policy authority and complete journal need independent custody; non-exportability alone is insufficient |
| Cost/capacity | Multiple voting custody domains, durable replication, majority-read/commit latency, complete journal/checkpoints and operational membership management | Actual device/service throughput, state binding, replacement and custody plus ordered-log costs are unknown |
| Availability/DR | Unreachable valid majority denies new permission; unknown work can cause indefinite downtime; all-majority loss has no approved recovery | Root unavailable/lost/uncertain likewise blocks; no approved reset/rebootstrap or orphan resolution |
| Review choice | Adequately bounded **request candidate**, not a selected consensus product/Production topology | Keep as an unselected alternative; do not borrow B's hypothetical protection to strengthen Q |

R1 has not produced a priced or measured winner. Its log now includes ADMIT, FIRST_USE, REVOKE and CLOSE transitions; costs cannot be represented as an epoch counter updated only on rare takeover. Batching and read optimization must preserve the specified durability/current-read semantics. No numeric capacity, latency, RPO/RTO or uptime is supported. These unknowns can be scoped/measured by later authorized work, rather than assumed closed before or after the request.

## 7. Is this new evidence or a repeat of S0-09F?

**The document itself creates no new security evidence.** It can motivate an experiment different from F only if it tests the actual surviving-quorum mechanism instead of reusing an assumed-current oracle API.

| Proposed future evidence type | Relation to F | Current status |
|---|---|---|
| Stub/single database/mock R promises monotonic head and durable OPEN; five wrappers expose that same promise | Repeats F's central assumption. Not evidence of quorum/root continuity; do not label it a real Lane2 proof | DESIGN_BLOCKED for the requested real-Q claim |
| Actual replicated state machine: durable majority commit/current reads, real minority state restore, learner quarantine/catch-up and committed admission/configuration | Could add measured consensus/restore/enforcement behavior not supplied by F, under the stated surviving-history premises | SECURITY_UNPROVEN; execution NOT_RUN |
| W history restored/lost while real Q retains complete journal; head/OPEN/idempotency replay checked | Could replace F's assumed W continuity with observed Q-backed history behavior for this limited fault envelope | SECURITY_UNPROVEN; execution NOT_RUN |
| Five containers or processes on one CI host | May give process/transport/storage-path observations; does not establish independent host, backup or administrative failure domains | SECURITY_UNPROVEN for independence; no execution here |
| Majority history rewind, all-root disaster recovery, physical same-identity clone, real nonreset hardware or restored old verifier without surviving mandatory enforcement | Not proved by the Q premise or by prior169 results; cannot be imported as a stronger conclusion | DESIGN_BLOCKED for automatic safety/recovery; execution NOT_RUN |

The novelty threshold is real protocol/state survival and route-enforcement evidence. Counting replicas, showing signed fresh nonces, assuming a non-restored controller, or demonstrating DENY after setting a loss flag is not that evidence. Even a later Q experiment passing every selected case proves neither absolute root irreversibility nor production custody separation.

## 8. Boundary and acceptance conditions for a permission request

These conditions apply R1's existing contracts; they are not execution permission or a new implementation plan.

1. **Name the experiment narrowly:** W and at most one/two minority-member restores against an already admitted current surviving majority, with a current independent mandatory guard. Do not describe it as safe restoration of R's own majority, root recreation or general Lane2 DR.
2. **Pin the actual mechanism and control envelope in the request:** implementation/version/correct membership semantics to be evaluated, members/configuration, preserved committed prefix, restore/backup rights and external guard/enrollment ownership. This review selects none of them. Do not enter authorization with an unspecified oracle substituting for the mechanism under test.
3. **Make all-route admission falsifiable:** inventory direct and established SQL/issuer/pool access, independently measured manifest/policy, old credentials/endpoints, restored-member vote/serve authority and effective quarantine. If this boundary is unavailable or bypassable in a supported mode, STOP; the review's request-readiness does not excuse it.
4. **Use actual durable history evidence:** complete OPEN/UNKNOWN, head/owner/policy, request-digest/idempotency and tombstones at the committed prefix; positive current-root authorization before faults; current-majority reads and exact restored checkpoint/suffix. Minority cannot self-promote or form a new accepted namespace. At configuration boundaries, use and verify the selected protocol's correct quorum rules, not a hardcoded count taken out of context.
5. **Separate logical ordering from local scheduling:** both grant/revoke orders, delayed response/new-transaction replay, no successor during unresolved old work, exact local outcome validation, member/transport failures and lost ACKs. Pre-ABORT and lost ABORT/CLOSE-ACK cuts remain explicit unrun obligations from F, not completed history. Prepared work must be explicitly prohibited/accounted for within the later authorized scope.
6. **Keep falsification and provenance:** live healthy positives, eligible contenders, reason-specific enforcement/OPEN/retirement/admission mutations, exact restoration and actual final-head evidence if execution is later authorized. Preserve the unchanged legacy D failure and prior inventory; no new combined169-run claim or inference of R proof from old CI.
7. **Keep every exclusion visible:** unavailable majority may cause observed DENY under a surviving guard; responsive majority rollback is not automatically detected by this contract. Majority-total-loss recovery, root/guard joint rewind, unsupported physical clones, Byzantine/privileged root control, orphan reconciliation, Production and general HA/PITR remain outside the proposed authorization.

The eventual Management request must supply its scope-specific custody/route inventory and measurable stop/failure criteria. That is request preparation, not a requirement to have already proved the implementation before requesting an experiment. If the applicant cannot supply an actual Q mechanism or mandatory enforcement boundary, this positive **scoping** vote does not carry over: keep that implementation/mode DESIGN_BLOCKED and return to targeted design refinement.

## 9. Claim ledger and residual P0/P1 risk

| Claim | Design/assurance status | Real-R execution status |
|---|---|---|
| W/minority restore contract under the specified surviving current Q and guard | DESIGN_SPECIFIED | NOT_RUN |
| Actual log durability, membership/learner safety and current-read correctness | SECURITY_UNPROVEN | NOT_RUN |
| Atomic head/OPEN/journal checkpoint and replay enforcement | SECURITY_UNPROVEN | NOT_RUN |
| Mandatory exclusion of old direct SQL/issuer/pool paths and retired policy | SECURITY_UNPROVEN | NOT_RUN |
| FIRST_USE/revoke logical order plus hold until positively verified outcome | DESIGN_SPECIFIED | NOT_RUN |
| Actual local scheduling, transaction replacement/replay and successor exclusion | SECURITY_UNPROVEN | NOT_RUN |
| UNKNOWN stays blocked after hard fence; no Lane2 clearing | DESIGN_SPECIFIED | NOT_RUN |
| Independent custody/backup/host separation, physical nonclonability, performance/cost | SECURITY_UNPROVEN | NOT_RUN |
| Guaranteed detection/safe automatic recovery of a responsive rewound majority or every root/verifier restore | DESIGN_BLOCKED | NOT_RUN |
| Lane3/manual/timeout orphan resolution or inference of real R security from the 169 prior observations | DESIGN_BLOCKED | NOT_RUN |

**Residual P0:** all actual Q and verifier/admission properties, exact durable OPEN/CLOSE/outcome behavior, own-majority rollback/rebootstrap and physical root/actor security remain unproved or outside scope. Historical C-only rollback stays **FAIL_SECURITY**. No original P0 is labeled empirically closed.

**Residual P1:** shared control/backup failure domains, policy/key distribution and member replacement operations, incomplete endpoint inventory, storage/compaction/replay correctness, capacity/current-read costs and potentially indefinite fail-closed downtime. Cost/operational assurance and test-result provenance are not supplied by this review.

## 10. Verification, references and final vote

Verification performed: read-only live main/R1/issue/prior-PR inspection; remote/local byte comparison, Git blob/content SHA256 checks, accepted-finding mapping and documentation diff/whitespace checks. The new review branch must add only this report relative to its main base. No code/SQL/migration/workflow/test was changed or executed and no CI was dispatched. An absence of automatically scheduled checks for a documentation-only diff is not a runtime PASS. Exact review SHA, Draft PR, final main/protected-head checks and delivery receipt are recorded in Issue28, avoiding a self-referential SHA in this document.

Primary references consulted for the delta (not a new vendor selection or a repetition of R0 research):

- [Pinned R1](https://github.com/alireza-anari/cac-project/blob/3dcd1c0896d05be2097ad7aa64f774a66e816043/docs/architecture/S0_09G_TARGETED_ROOT_REFINEMENT_R1.md), the 108 lines cited above; [accepted R0 review](https://github.com/alireza-anari/cac-project/blob/e63b16a0916aa6a43d5a36a20027dab20b506464/docs/security/S0_09G_ROOT_DESIGN_READ_ONLY_REVIEW.md); [management R1/acceptance comment](https://github.com/alireza-anari/cac-project/issues/28#issuecomment-6686557755). Repository documents define the proposed CAC contract, not physical security evidence.
- **[T1]** [Ongaro/Ousterhout, Raft extended paper](https://raft.github.io/raft.pdf), sections5.4,6–8: committed-history safety, membership continuity, persisted state, client idempotency and current reads require more than majority arithmetic. This is protocol context, not adoption of Raft or proof about an unspecified implementation.
- **[T2]** [etcd learner design](https://etcd.io/docs/v3.6/learning/design-learner/), Raft Learner / Features: non-voting catch-up and checked promotion illustrate admission obligations; a learner is not merely another vote. No etcd deployment/product approval or version capability certification is implied.
- **[T3]** [etcd disaster recovery](https://etcd.io/docs/v3.6/op-guide/recovery/), Revision Difference / Restoring from snapshot: restoring old history can lower revisions and recreate logical identity. Such recovery guidance is not an independent CAC majority-rollback witness.
- **[T4]** [etcd API guarantees](https://etcd.io/docs/v3.6/learning/api_guarantees/), strict serializability/current reads and operation completion: weaker read modes and uncertain replies cannot replace the specified current-root decisions and idempotent committed-state lookup. This does not establish CAC's root authenticity or restore safety.

**Final vote for Astra Management: READY_TO_REQUEST_BOUNDED_QUORUM_SURVIVAL_POC, only within R1's surviving-current-majority and mandatory-current-guard premises.** The five R0 contract deficiencies are sufficiently specified or explicitly bounded for that request; empirical security remains open. An actual replicated/journaled/minority-restore experiment can add evidence beyond F; another assumed oracle cannot. There is no execution authorization, general real-root anti-rollback acceptance or Production/protocol approval.

Lane2 implementation remains unauthorized; Lane3/orphan clearing and SOURCE-001/GATE-SOURCE remain BLOCKED. Issue28, Issue23 and Gate9 stay OPEN. All prior PRs remain Draft/unmerged. R0/R1, APRs and prior tests/results remain unchanged; no Sprint0 or historical-source/baseline acceptance is issued.
