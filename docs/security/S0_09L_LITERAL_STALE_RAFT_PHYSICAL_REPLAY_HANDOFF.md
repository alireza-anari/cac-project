# S0-09L — literal stale Raft minority replay handoff

NEW_IMPLEMENTATION_EXPERIMENTAL / CURRENT_NONRESTORED_MAJORITY_ONLY / NO_PRODUCTION.

## Authority, source and delivery gate

Issue [#47](https://github.com/alireza-anari/cac-project/issues/47) and
`docs/architecture/S0_09K_ARCHITECTURE_RULING.md` at management main
`7a2791504a8cfd32ae83e239c51cf28e75611cc7` authorize this disposable experiment.
Technical parent: K `9e768a4d1f6c97c429c36475237e132b8e3e7fc2`.
Branch: `work/s0-09l-stale-raft-minority-physical-replay`.
Draft [PR #48](https://github.com/alireza-anari/cac-project/pull/48) targets
`work/s0-09k-policy-retirement-experiment`. No previous PR, main code, SQL,
Preview, APR or inherited test is changed.

Test-first checkpoint: `800c8d2ecc636328e002154d64d3dc72e5b313a9`.
Initial physical implementation: `60efe68a1eccf387577ed5b8c2607f413808c9a4`.
This report also accompanies the subsequent L-local termination-proof fix and
seventh test. Its final SHA, synthetic merge and completed CI receipt belong in
the external Issue #47 / PR #48 delivery ledger; a file cannot contain its own
commit hash. **Until those corrected-head receipts pass, final status is
L_INCOMPLETE.** Initial six-test evidence below is not extrapolated to test07.

## Design decisions and scope

The pre-existing H controller deliberately never imported native old bytes.
L adds only `experimental/backend/h_quorum/l_physical/` plus its workflow/report.
Keeping L inside the H experiment preserves F's existing backend provenance check
without weakening that check. The first top-level package placement caused an
explicit provenance CI failure and was moved; it was not a security assertion failure.

The selected approach is a stopped full member data-dir copy, with exact file
hashes before native restart. Logical etcdutl snapshots, app journal replay or a
fresh learner alone cannot establish the requested physical import and are not
substituted. Rewriting native member metadata or using force-new-cluster is not
allowed. Only r4 is stopped/replaced; original r1/r2/r3 identities, PIDs and data
paths stay intact. The corrected helper additionally requires all three local
state values/revisions to equal the current Root state. No same-ID member runs
concurrently. The process-stop wrapper preserves the original PID record and
waits for its executable to disappear before any copy/rename/spawn, including
an inherited non-child SIGKILL branch.

This is a test harness, **not** an etcd operational recovery recommendation.
Official upstream [runtime reconfiguration](https://etcd.io/docs/v3.6/op-guide/runtime-configuration/)
describes removed-member exits; [data corruption recovery](https://etcd.io/docs/v3.6/op-guide/data_corruption/)
distinguishes member replacement/persistent-state repair from whole-cluster
recovery. Those documents motivated expectations; only executed native commands
and assertions below count as L evidence.

## Physical procedure and actual commands

The pinned inherited fixture runs etcd **3.6.16** (upstream release SHA-256
`c8c0d96d8292ef085deabbf735e9561d3d396768e4d606df005aa25964f21911`),
PostgreSQL **17.11**, PgBouncer **1.22.0-1build4**, Python **3.12.15**.
Five real voting processes and three PG clusters share one disposable Actions
host and administrative plane. There is no claim of independent physical custody.
No Docker executable is available in this local workspace; actual execution is
in the authorized disposable CI, not a claimed local database run.

`fixture.Physical` implements these exact operations on privately owned paths:

1. Read authenticated current membership/status and current Root state. Preserve
   original r1/r2/r3 identity/PID/data paths; never restore their files.
2. Stop only r4 using owned PID SIGTERM; inherited timeout can use SIGKILL. L's
   wrapper independently waits on the retained original executable identity.
3. Restart that same member with `--snapshot-count=10`, then issue 40 real
   `/v3/kv/put` requests under random `/cac-l-snapshot/` keys. Require genuine
   `member/wal/*.wal`, `member/snap/*.snap` and `member/snap/db`.
4. Observe actual r4 state/member ID and complete journal. Stop/prove termination,
   `shutil.copytree(data_dir, archive)`, SHA-256 every file and require source/copy
   inventory equality. These are native files, not a logical key export.
5. Advance Root using authenticated control `retire_policy(expected=1,new=2,
   request=<UUID>)`, or actual epoch advance for the authority sensitivity case.
   OPEN/UNKNOWN remains in the current majority's full ordered state.
6. Stop/prove r4 termination, `Path(data_dir).rename(private_quarantine)`, then
   `shutil.copytree(archive,data_dir)`. Require every restored file size/hash to
   match the archived inventory **before** spawn. No ID/term/WAL rewriting occurs.
7. Start native etcd and separately require current member ID, exact current
   Root state/revision and byte-identical complete journal rows. Native catch-up,
   unavailable endpoint and native refusal are distinct observed results.

The native command (the actual argument list is in `fixture.py:Physical.spawn`)
is the following, with variables resolved from the private synthetic fixture:

```sh
"$ETCD" --name "$NAME" --data-dir "$DATA" \
  --listen-client-urls "$CLIENT" --advertise-client-urls "$CLIENT" \
  --listen-peer-urls "$PEER" --initial-advertise-peer-urls "$PEER" \
  --initial-cluster "$CURRENT_MEMBER_URLS" --initial-cluster-state existing \
  --initial-cluster-token "$ROOT_ID" --client-cert-auth=true \
  --trusted-ca-file "$CA" --cert-file "$CERT" --key-file "$KEY" \
  --peer-client-cert-auth=true --peer-trusted-ca-file "$CA" \
  --peer-cert-file "$CERT" --peer-key-file "$KEY" --logger zap --log-level info
# Only snapshot preparation adds --snapshot-count=10; replay uses unchanged defaults.
```

TLS/auth and strict membership checks stay enabled. Source paths are confined to
owned private fixture directories, reject symlinks and other members' data dirs.
Raw WAL/db files contain synthetic auth state and are **not uploaded**. Safe
artifacts contain exact per-file hashes, source identities and filtered native
messages, not credentials or raw private logs.

## Actual initial native evidence

Initial PR sensitivity job
[128837696977 / run42515568008](https://github.com/alireza-anari/cac-project/actions/runs/42515568008/job/128837696977)
completed SUCCESS at `60efe68...`. It executed original probe, deliberate
reason-specific RED/exact restoration/same GREEN, then **six** real methods in
**171.065s**, no skips. Push sensitivity job128837681164 in
[42515562501](https://github.com/alireza-anari/cac-project/actions/runs/42515562501)
also completed SUCCESS. Completed job receipts remain valid even if the longer
whole workflows are superseded by the corrected source commit.

One concrete L00 provenance chain from that PR job:

- R cluster `1814548152912022310`; original survivors r1
  `10651514712806684383`, r2 `15615458713629906546`, r3 `5194343650252585428`.
- Archived r4 ID `8173303404284850787`, policy1, seq14, revision187, head
  `85719d9e7f8c57f712dfc7ff9c3f7641f80d15f8e5688a5effc8f1e5549a2a3b`.
- Native `member/wal/0000000000000000-0000000000000000.wal`, 64,000,000 bytes,
  SHA-256 `9092ffcfc2d592d2a1032aad6fce86876e891c77de77646663d442acdccea11d`.
- Native `member/snap/0000000000000002-000000000000016e.snap`, 10,893 bytes,
  SHA-256 `a2e7232160eff0620e35a82c9119d8c12955a5fb10580ecdfb44bcb3f827a3ff`.
- `member/snap/db`, 16,801,792 bytes, SHA-256
  `c2e4e6e04bab79d84a2865fc7f9a28730e5c37bec9376986f82c00b24c3a9711`.
- After actual reimport/restart, **same r4 ID**, policy2, seq15, revision228,
  complete journal16, current head
  `001a4c0a03ecc3d6ba1416046c44fc6f81dd446cfdfead496922904379ac7003`.
- PG system IDs A `7705885880685178918`, B `7705885881861627942`,
  C `7705885885797695525`; pooled PID494, old xid861/new xid880. Retained old
  context was denied, current-policy scoped SQL succeeded.

The removed-member case actually restarted old ID8173303404284850787 after
native replacement learner5516151659508694407 was stopped. Native log reported
`restarting local member`, hex ID `716d682465e3b263`, then
`etcdserver: the member has been permanently removed from the cluster`, exit1.
The incompatible learner-config case supplied old ID5516151659508694407 bytes
under new learner1481707832052526085 configuration; native log identified old
hex ID `4c8d4eb560327d87`, same permanent-removal error, exit1. The valid fresh
learner directory was then reinstated, caught up and explicitly promoted through
native consensus. No timeout was treated as permission to vote or clear UNKNOWN.

## Test matrix and commands

`python -m h_quorum.l_physical.run` fails on any failure/skip and requires seven
methods. `python -m h_quorum.l_physical.sensitivity` runs the one original
physical-import assertion before/under/after a controlled one-check mutation.
`python -m h_quorum.run` preserves H51; `python -m h_quorum.policy_run` preserves
K17. Existing workflows run inherited169 (94+C20+D15+F40). Total inventory is
**244 distinct methods if the final corrected-head suites complete successfully**;
repeats, mutation/scanner probes and the extra historical D failure are separate.

| Method | Required behavior | Initial60efe68 observation / final gate |
|---|---|---|
| L00 | Actual stopped byte reimport and same-ID catch-up; old policy readiness/issuer/ADMIT denied; same PgBouncer PID/new xid old context denied, healthy policy2 positive | PASS for initial method; added offline pre-replay negatives await corrected-head receipt |
| L01 | Archive omits later OPEN/grant; current R retains operation through actual protected COMMIT; successor blocked until known CLOSE, then B succeeds | PASS |
| L02 | First-use denied after cut produces UNKNOWN; native replay cannot clear it, fake ABORT/adoption/successor denied | PASS |
| L03 | Removed old-member bytes actually booted and native-refused with old ID/exit1; valid fresh learner recovery | PASS |
| L04 | Fresh learner configuration receives actual incompatible old bytes; native old ID/refusal/exit1; correct directory catch-up and promotion | PASS |
| L05 | Actual native replay across real epoch advance, then non-control policy retirement denied; control transition and healthy policy2 succeed | PASS; original controlled sensitivity also demonstrated |
| L06 | Real SIGSTOP forces non-child SIGKILL; retained original PID termination is proved before reimport, then healthy policy2 succeeds | Added after review, NOT_RUN at report-writing checkpoint; final receipt required |

The original missing-feature RED ran after a real healthy SQL baseline in push
[42514945640](https://github.com/alireza-anari/cac-project/actions/runs/42514945640)
and PR [42514949962](https://github.com/alireza-anari/cac-project/actions/runs/42514949962)
at800c8d2...: `Literal native Raft archive/reimport fixture is not implemented`,
one assertion failure/exit1. It is not a native import result or security exploit.

Initial sensitivity used synthetic policy state only: after actual native import,
the deliberate control-role-check mutant let coordinator commit policy2 and the
**original** assertion failed: `Physical replay accepted non-control policy retirement`.
Parent restored exact `retirement.py` bytes/SHA-256
`c619aa3043e1342d97c50b814e14c95b98a586688442cb43b27c0668d4d29652`,
restarted current service and required identical R policy2/revision113 state.
The same original test GREEN used a separate fresh synthetic namespace; earlier
R history was retained, never rolled back or used as an orphan reset. Only the
restored implementation can earn GREEN; no weakened security check is accepted
as successful behavior. Main/production services and data are not involved.

## Independent review, corrections and limits

A fresh role-separated read-only reviewer examined exact initial candidate source,
assertions, workflow and physical provenance design, without running tests or
reading private fixtures. No P0/P1 source defect was identified in that review.
Two P2 observations were recorded:

1. Retained old serializable response is **not injected into admission**. All
   initial authorization negatives occur after native current catch-up. L does
   not prove rejection of a live available stale minority response used as the
   authority input. This stays **NOT_RUN**; genuine stopped-endpoint unavailability
   and current-authority denial are separate executed cases. No fake response
   injection is substituted for native input.
2. Inherited `Cluster.stop` may clear a non-child PID immediately after SIGKILL.
   L now retains the original process record, waits for executable absence and
   rechecks before spawn; L06 executes the actual forced non-child branch. This
   is an L-local corrective proof requirement, not a change to H or a claimed
   previously observed overlapping member. Its actual final test must pass.

The corrected helper also proves that all three original local state values and
revisions match current Root before/after replay, beyond unchanged identity/PID.
Final-review and corrected-head evidence status is recorded in the external
handoff ledger. A source review/selected-log audit is not external certification.

| Residual or excluded scenario | Status |
|---|---|
| Responsive restored R majority, all-root recovery, simultaneous old verifier/root restore, physical admin/key independence | NOT_RUN / unsupported; GLOBAL_FAIL_CLOSED_NOT_ESTABLISHED |
| Available stale serializable minority response supplied as authoritative guard input; packet-level lost native Raft ACK | NOT_RUN; actual unavailable stopped endpoint is a different executed condition |
| Crash-consistent archive while writer remains live, corrupted/torn WAL, every compaction/snapshot/crash cut | NOT_RUN; archived data is from a proved-stopped member |
| General semantic policy migration, existing pre-K namespace upgrade | NOT_DEMONSTRATED / outside scope |
| UNKNOWN/orphan reconciliation or successor release from timeout, membership repair or process absence | BLOCKED / Lane3; potentially indefinite downtime |
| Historical S0-09D C-only rollback | FAIL_SECURITY; unchanged harness reproduction must remain visible |
| Compromised common administrator/controller/guard or real independent custody | NOT_RUN; inherited trusted lab assumptions |

All previous 237 distinct tests remain byte-identical; scope receipts compare the
entire parent backend except the new L subdirectory. No SQL/migration, actual
product integration, IdP/MFA, public deployment or Preview change is introduced.
SOURCE-001/GATE-SOURCE remain BLOCKED, Gate9 and #23/#28/#33 OPEN, E G1–G5
DESIGN_BLOCKED, protocol PROPOSED. PR48 and prior PRs remain Draft/unmerged.

## Decision rule

Recommend `L_STALE_RAFT_MINORITY_CURRENT_Q_BOUNDED_PASS` only after the final
corrected-head push/PR/synthetic-merge receipts demonstrate L7, H51, K17 and
inherited169, including the explicit forced-stop control, with safe source and
artifact scans. Until then L_INCOMPLETE. A supported stale-authorization assertion
failure is L_SUPPORTED_SECURITY_FAIL; inability to execute authentic native import
is L_PHYSICAL_IMPORT_NOT_RUN. No whole-root rollback, protocol, Production or
Sprint0 acceptance follows from any L result; Management alone interprets it.

## Corrected-head failure under investigation

At `0d8fa55f6a8f724353a2f6bdf87d24f686d42ac1`, PR sensitivity job128841073583
in run42516623015 and push sensitivity job128841054392 in run42516618574
ran L7 and failed L06 with `RuntimeError: Real etcd readiness blocked` in
`caught_up()` after the actual SIGSTOP/non-child SIGKILL and native reimport.
The executable-absence and child exit(-SIGKILL) assertions had completed; L00–L05
passed. This is a real convergence/fixture error, not a demonstrated stale
authorization, and it is not suppressed or counted as PASS. Final verdict stays
L_INCOMPLETE. A following diagnostic checkpoint adds filtered native messages,
last local head/revision and native exit state, plus an isolated L06 preflight;
no security assertion, deadline or Raft state is relaxed to obtain GREEN.
