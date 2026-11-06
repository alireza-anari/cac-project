# S0-09H independent read-only source/security review

Status: **bounded experimental source review; no Production/protocol acceptance**. Requested by Issue31. Separate read-only reviewer `s009h_builder_check` returned these findings and addenda; the implementer transcribed the report. Reviewer did not edit source or execute security tests.

## Scope and verdict

Whole-source review pinned to `6daf110d2677974f019363bf3ebf1c503218b66f`: actual R/journal, current profile/admission, online signed guard, W replay, owned PG observer, SQL/RLS, learner controller, real crashes/pool/reply loss, H05 and workflow. Subsequent scanner/test/workflow fix and combined W+minority live-OPEN test delta were separately reviewed read-only with no further material finding.

No demonstrated P0/P1 unsafe outcome was found in reviewed source **under current non-restored majority and trusted PG observer/controller assumptions**. This is not root rollback resistance or general security acceptance. The source retains linearizable R reads, atomic state+journal CAS, durable OPEN before grant, grant/revoke ordering, exact PG transaction binding, unresolved exclusion and conservative UNKNOWN. Current external profile/catalog, private legacy ACL restrictions and complete W replay remain mandatory. Reply-loss fixtures observe real upstream ACKs before withholding downstream responses.

Passing source review does not turn pending/cancelled workflows into PASS. SHA-specific complete empirical results and source receipts must accompany management delivery in Issue31. #9/#23/#28 remain OPEN, SOURCE/GATE-SOURCE BLOCKED, historical D rollback FAIL_SECURITY, protocol PROPOSED.

## Findings and disposition

| Finding | Evidence and disposition |
|---|---|
| Missing non-view rewrite-rule catalog coverage | Earlier independent finding reproduced via actual quarantined CREATE RULE at d5549ca/Push42276748650. Minimal a62c24e fix; original inequality plus exact DROP restoration GREEN in H28 Push42277774966/PR42277781116. No general catalog certification. |
| P2 runtime hook also intercepted issuer COMMIT | Actual59d4004/Push42282804619 matched review. Fixed by installing hook after issuance and runtime UPDATE; original assertions retained, actual cut successful in4aa logs. |
| Draft P1 current-head mutation disabled aggregate guard | Aggregate require=RETURN removed. Corrected mutant selects an authenticated ancestor for readiness only; binding/W/nonce/signature checks run and actual current ADMIT still denies old A. RED is stale readiness, **not an RLS bypass claim**. |
| Draft P1 replay witness repaired by ADMIT | Recovery04 now corrupts after actual admissions/grants and directly reads protected scope before any coordinator repair; accepting mutant independently verifies W row still absent. |
| Draft P1 worker-only cleanup missed timeout/death | Parent now owns exact source restoration/current-service reload and independently verifies SQL/catalog/ACL/NOLOGIN from receipt durable before LOGIN mutation. Parent quarantines after abnormal worker exit; no later probe on cleanup failure. |
| P2 policy retirement untested | Policy remains1. Supplied0/True negatives do not prove actual retirement. **NOT_RUN**; real signer retirement is separate. |
| P2 fixture credential scanner incomplete | Original6daf missed nested passwords, anchor_password, proofs and arbitrary signer IDs. Local synthetic regression failed five subcases; safe positive passed. Minimal recursive known-field/container fix made same two methods GREEN. Reviewer source addendum found fix adequate; no leak observed. Final-head CI required. |

Scanner delta hashes: scan.py SHA256 `2d5649dd5ef5290bbf12845baf1ba6a9deec5b7f824c9cd60133546ff40279a8`; test_scan.py `443db7161f1d20312d139bb23bf31675b54f6e0274c223904699a15a37710720`. Literal known-value matching is not universal DLP or proof that arbitrary operation capabilities cannot leak.

Combined recovery delta snapshots W before the exact live operation, verifies restored W omits its UUID while actual R OPEN remains unchanged, replays current complete R, executes legitimate SQL, and performs both fresh learner recoveries before known close. Source review found it sound; execution pending at review cut. It does not perform literal old Raft snapshot import.

## Empirical review boundary

Reviewer independently inspected e182e886 PR job128112459575: synthetic merge7ab92ce187c12c4a263280c65abbb08c9b50e106,31 methods/no skips, actual W/B restores, old-A denials and current-B write. W31 snapshot followed closed operations; unresolved OPEN required a separate test.

Later4aa Push42284999970/PR42285007782 ran43 methods: preceding42 successful, final live-OPEN learner maintenance readiness blocked. Logs support11 actual SIGKILL cuts, live-OPEN W rollback/current-service restart, real PgBouncer PID/fullxid reuse and user cancel, PREPARE55000/IDLE->Denied/UNKNOWN and actual majority outage. This is **not whole-suite PASS**. Controller post-start voter-token refresh and new H51/reply-loss/H05 need their own complete repeat evidence.

At6daf, Push42287466650/PR42287478003 reported sensitivity step success (five baseline/target RED/exact restore/same GREEN controls and clean git diff); whole/post-mutation suites were still pending at this cut. Complete logs/source receipts, not this source report, establish OBSERVED_PASS.

## Residual P0/P1 boundaries

- Responsive rewound majority, majority/all-root restore, physical same-identity clones and independent cloud/admin/backup/key custody remain excluded/unproved. Current guard cannot detect coherent majority rollback without an independently surviving newer fact.
- Literal old snapshot import into a live learner is unsupported/NOT_RUN. Fresh quarantined learner replacement is different; application journal equality is not internal Raft WAL byte equality.
- Raw coordinator credentials can assert bindings/outcomes. Malicious observer/controller resistance is unproved; one host/user and multiple processes/containers do not establish operational independence.
- UNKNOWN/orphan clearing stays prohibited after session death, timeout, hard fence or idle backend. Intentional mutant histories remain quarantined in old test namespaces; restoring source never rewinds R or clears them.
- Journal growth/retention/compaction, capacity, latency, sustained concurrent writers/close availability, multi-site partitions and operational DR remain unmeasured. Experimental signing/key/TTL fixtures are not contracts or technology selection.

Any supported old-owner authorization, forgotten unresolved hold, successor READY overlapping possible old COMMIT, stale route bypass or guessed release outside isolated intentional mutation requires FAIL_SECURITY and stop.

**Recommendation:** management may assess only completed SHA-pinned `Q_SURVIVAL_INTEGRATION_EVIDENCE_UNDER_NONRESTORED_MAJORITY`. No Lane3, Production, protocol, baseline or Sprint0 acceptance is issued.
