# S0-09M — native same-ID member availability triage

NEW_IMPLEMENTATION_EXPERIMENTAL / P1_AVAILABILITY_OPEN / NO_PRODUCTION.

## Authority and frozen finite plan

Issue #49 and `docs/architecture/S0_09L_ARCHITECTURE_RULING.md` at management
main `bd716dd2049fe08f3c766a646883dd403c43eb4f` authorize this diagnostic slice.
Technical base is exact L `ba5bc82170da4523b39b1512eb7d2de344255c3a`.
Branch: `work/s0-09m-native-member-availability-triage`, stacked Draft against L.

Before implementation/results, freeze the following matrix. **Two repetitions
per case per CI trigger**, one fresh disposable five-voter/three-PG lab per
observation. No outcome-dependent rerun or additional cases to force reproduction.

| Case | Post-archive r4 progress | Stop before Root advance | Bytes used at final start |
|---|---|---|---|
| OFFLINE_OLD_CLEAN | None: stays stopped after archive | Original clean SIGTERM | Exact old archive |
| PROGRESSED_OLD_CLEAN | Resume, 16 fixed witness puts, verify local application and higher Raft index | Clean SIGTERM | Exact old archive |
| PROGRESSED_OLD_KILL | Same bounded progress | Actual SIGSTOP, non-child SIGKILL, termination proof | Exact old archive |
| PROGRESSED_CURRENT_KILL | Same bounded progress | Same forced stop | Sealed current data-dir, **no old-byte import** |

The last row is a current-file crash/restart control, not a substitute for physical
replay. Compare the two progressed old-file cases for stop-type effects, and the
two forced-stop cases for file-version effects. Authentication/status calls may
also advance Raft; record measured indices, never invent an exact five-entry gap.
Independent labs avoid unapproved repair/reset between samples. No member repair
is executed in new M samples; report fresh-learner repair from the separately
preserved L regressions as a different evidence cohort.

Implementation plan (inline, one role-separated final source/log reviewer):

1. Preserve real L source and original final proof log. Run a healthy real PG/R
   baseline plus missing-M-driver assertion RED in the disposable CI.
2. Add only `h_quorum/l_physical/m_*` diagnostics/tests and own scoped workflow.
   Existing L/H/K assertions, Raft binary, SQL, Preview, APRs and architecture
   documents remain unchanged. All prior244 distinct methods are retained.
3. Observe archive/pre-stop/current/post-restart native identities, file hashes,
   highest/applied indices, stop and native child exit, elapsed time and complete
   current Root state/journal. Protect original r1/r2/r3 PIDs/IDs/data paths.
4. Keep a real pre-granted PG transaction OPEN across the native observation;
   require unchanged Root/ordered journal before any known local outcome. Commit
   only with actual local ACK/authorized CLOSE. Then deny old policy and require
   healthy policy2 SQL before teardown or any repair. L7 separately retains its
   genuine UNKNOWN test; no M-created UNKNOWN is cleared.
5. Classify CATCH_UP_SAME_ID, NATIVE_REFUSAL_EXIT1, NATIVE_FAIL_STOP_EXIT2,
   TIMEOUT_UNRESOLVED, TEST_HARNESS_FAILURE separately. A wrong current-admission
   result is M_SUPPORTED_SECURITY_FAIL and takes priority. Native panic is
   availability failure even when an observational test/CI passes.
6. Execute frozen M observations, preserved L7/K17/H51 and inherited169 with
   exact-head Push/PR receipts, independent review and final Issue #49 ledger.

## Provenance review / execution ledger

2026-11-14: live main and L PR48 matched supplied SHAs; PR48 remains Draft/unmerged.
Original L PR proof run42517949002/job128844979431 was read again. It records
actual native exit2 with `tocommit(3015)` beyond `lastIndex(3010)`, separate
fresh-learner repair, and seven completed methods. This is historical evidence,
not an M observation. Local source was recovered from GitHub after workspace
maintenance; exact L checkout verified. No local Docker executable is available;
actual native/database execution will use the authorized disposable CI.

Ruling: use fixed isolated sample jobs rather than automatically repairing a
member between M observations. Cost: additional disposable job bootstrap time;
benefit: no implicit member-removal or operational recovery authorization.

## Diagnostic calibration (not final M cohort)

Test-first RED commit `1dce5c82c1ba2a42070b02904b81520feee9ad63`:
push run43629539092/job132552875913 and PR run43629542232/job132552885858
failed the missing-driver assertion after the real healthy PostgreSQL baseline.
No security checks were disabled.

First driver commit `c63925b91192e1af18d3ad6382b8cdf6c2ecac42` ran the frozen
matrix but its clean-progressed cases rejected actual native exit -15 as if only
zero could represent normal shutdown. These are **incomplete diagnostic samples**,
not completed native availability results. Other completed rows remain preliminary
receipts and are not substituted for the final fixed cohort.

Exact etcd source `0b065e61c679ea81f6862bb24c9815f7fc673966`,
`pkg/osutil/interrupt_unix.go`, calls handlers, restores the default signal action,
and re-sends the original SIGTERM. The M-only calibration now requires BOTH native
`received signal; shutting down` (`signal=terminated`) and `closed etcd server`,
and actual child exit 0 or -SIGTERM. It never treats SIGKILL as clean. All exit
values are retained. This corrects a diagnostic assumption, not a Raft/security
control. The fixed cases, two repetitions and files/authority cuts stay unchanged.

Independent source review also required: record actual archive-stop exit rather
than hardcode zero; distinguish typed transport, TLS/auth/protocol probe errors;
complete independently possible security checks before failing native diagnostic
classification; and mark an accepted policy1 ADMIT as M_SUPPORTED_SECURITY_FAIL.
Corrections are M-only. Final-head execution/log review remains pending.

## Reproduction and evidence contract

Only the disposable CI workflow `native-member-triage.yml` provisions the fixture:
three independent PostgreSQL17.11 containers, five real etcd3.6.16 voting processes,
mutually authenticated transport and inherited controller/SQL guards. Python3.12.15;
PgBouncer1.22.0-1build4 is installed for preserved regression cohorts. All processes
share one Actions host/admin plane; this is not independent physical custody.
Release SHA-256 is `c8c0d96d8292ef085deabbf735e9561d3d396768e4d606df005aa25964f21911`.
Postgres image digest is
`839fbb5a4942a7758dd93e18b42ea5649807491a0545b5eeeb8f0b8bb11857a5`.

Actual workflow commands, working directory `experimental/backend`:

```sh
python -m recovery_fencing.lab
python -m h_quorum.cluster
python -m h_quorum.service
# One selected frozen case/repetition per fresh disposable job:
python -m h_quorum.l_physical.m_run
# Separate original cohorts, no assertion substitutions:
python -m h_quorum.run
python -m h_quorum.policy_run
python -m h_quorum.l_physical.run
python -m unittest -v h_quorum.tests.test_scan
python -m h_quorum.scan
```

`CAC_M_CASE` is one of the four table names; `CAC_M_REPEAT` is 1 or 2.
Generated private config paths and credentials are never report artifacts.
`Physical.spawn` preserves the exact L command/flags: existing same-ID native
etcd data-dir, peer/client mutual TLS, original cluster token, no force-new-cluster
or WAL rewriting. The archive setup uses `--snapshot-count=10`, forty fixed
snapshot-witness puts and full stopped `shutil.copytree`; inventories require WAL,
`.snap` and `member/snap/db`. M records full SHA-256/size per file before restart.

The progressed cases restart current r4 files and apply sixteen explicit witness
puts. Auth/status traffic can add entries; the assertion is at least sixteen
additional applied entries, not an invented exact total. Forced-stop cases issue
SIGSTOP, then use the inherited owned non-child stop wrapper (TERM then bounded
SIGKILL); original PID/executable absence and actual child -9 are required. Only
r4 files are renamed/restored. Current-file control uses its own sealed latest
files. Original r1/r2/r3 voter IDs/PIDs/data paths and local current Root are checked
before archive, before replay, after native observation and after healthy SQL.

Each observation emits safe `M OBSERVATION` JSON with real member/cluster IDs,
archive/current/imported file receipts, Raft term/index/applied-index, native
exit/panic/stack, elapsed interval, original-majority IDs and direct-PG PID/fullxid/
systemID. Exact full Root state and ordered journal equality is asserted across
replay with a genuine pre-granted OPEN. The earlier authorized write commits only
on actual local COMMIT ACK and exact authoritative CLOSE, then current-policy2
SQL must succeed and new policy1 admission/readiness must be denied **before any
repair or teardown**. No M member is repaired; no M UNKNOWN is created or cleared.

Only allowlisted credential-scanned proof/topology/quorum/source receipts are
uploaded for thirty days. Native raw logs, TLS paths, private config, database
contents and native data archives stay private/temporary. Archive hashes establish
provenance within the disposable job, not future reproducibility of random bytes.
Local AST/scope/whitespace checks are not native database execution; local Docker
was unavailable. CI is the actual runtime evidence.

## Source-level bounded explanation and limits

Pinned etcd source at `0b065e61c679ea81f6862bb24c9815f7fc673966`
[`server/go.mod`](https://github.com/etcd-io/etcd/blob/0b065e61c679ea81f6862bb24c9815f7fc673966/server/go.mod)
uses Raftv3.6.0. The annotated upstream tag resolves to immutable Raft commit
`f35a02212416d045c574e30aa59d4b07c4b8d732`.
[`log.go:320`](https://github.com/etcd-io/raft/blob/f35a02212416d045c574e30aa59d4b07c4b8d732/log.go#L320)
panics when a requested higher commit index exceeds the local lastIndex.
[`raft.go:1830`](https://github.com/etcd-io/raft/blob/f35a02212416d045c574e30aa59d4b07c4b8d732/raft.go#L1830)
passes a received heartbeat's Commit into commitTo.
[`raft.go:692`](https://github.com/etcd-io/raft/blob/f35a02212416d045c574e30aa59d4b07c4b8d732/raft.go#L692)
sends heartbeat Commit as min(remembered follower Match, leader committed).
These are source semantics, not proof of the runtime leader's private progress.
A matching captured stack plus actual panic numbers supports a bounded immediate
failure explanation. It does not prove why that heartbeat value arose. Remembered
higher follower-match state is a **hypothesis**, not an experimentally measured
root cause. No leader-internal/wire instrumentation or algorithm change is made.

## Independent source review

A role-separated read-only reviewer evaluated corrected code SHA
`37daa456da7251e0a356b231db4019ef2232db68`. Four P2 diagnostic/evidence findings were
corrected: actual archive-stop status, typed probe errors, security-priority checks
before final harness verdict, and wrong-admission labeling. A minor current-policy
binding label was also corrected. No remaining blocking source finding was reported.
The reviewer ran no infrastructure or native tests. Log review is a separate gate.

The reviewer specifically limits conclusions: finite separate labs do not isolate
all leader/term/timing effects; catch-up is a current-state/journal observation,
not future durability; panic is P1 fail-stop even if the diagnostic passes; no new
M repair is tested; M SQL uses **direct PostgreSQL**, while PgBouncer evidence is
from separate preserved H/K/L suites; UNKNOWN remains a separate preserved L
regression, never an M reconciliation claim. These limits are part of acceptance.

## Risks, technical recommendation and unexecuted scope

| Priority / scope | Status | Consequence / recommendation |
|---|---|---|
| P1 native same-ID old-file recovery availability | OPEN | Keep restored minority quarantined until positive native current-state/journal proof; diagnostic PASS is not remediation. |
| P1 precise triggering mechanism | HYPOTHESIS beyond bounded native condition | No necessary/sufficient timing or leader-cache claim; no probability estimate from finite observations. |
| P1 automatic repair / operational recovery | NOT_RUN in M | No recommendation to import old files in Production. Any new learner repair needs separately accepted operational procedure; inherited L evidence remains distinct. |
| P0 majority rollback / full root loss / physical clone independence | OUT_OF_SCOPE / SECURITY_UNPROVEN | Original current majority is mandatory; no rollback-root security inference. |
| OPEN_UNKNOWN reconciliation / Lane3 | BLOCKED | No timeout, absent response or member repair authorizes clearing an unresolved operation. |
| Compound M pooled replay and M UNKNOWN | NOT_RUN | Direct-PG M and separate inherited pool/UNKNOWN tests must not be conflated. |
| Other etcd versions, multi-host faults, disk corruption, network partitions, long soak, leader instrumentation | NOT_RUN | Finite pinned single-host matrix only; no general recovery guarantee. |
| Evidence lifetime / custody | P2 | Safe Actions artifacts expire after thirty days; retain run/job ledger and report. No private archives published. |

Only a bounded descriptive diagnosis is requested. Do not patch Raft, disable
security checks or auto-repair on timeout. Keep P1 open until a separate accepted
remediation/operational workaround has its own evidence. A failed member can reduce
redundancy even while current majority and PostgreSQL remain available. Surviving
3/5 permits consensus but does not prove tolerance of another member failure.


## Measured corrected-code cohorts (2026-11-15, UTC logs)

Code SHA `37daa456da7251e0a356b231db4019ef2232db68`; tested PR synthetic merge
`d79bbf78a27bba1e0353af24ec5e7cd3908434f1`. Each cohort has exactly eight completed
single-observation jobs; repeated methods are not additional distinct tests.
A live member has native exit `null` at observation, never an invented zero exit.
The following jobs completed successfully as **diagnostics**; their panic outcomes
remain P1 availability failures. Whole workflows also contain separate long-running
regression jobs; those must not be inferred successful from sample completion.

### Push — [run 43682789400](https://github.com/alireza-anari/cac-project/actions/runs/43682789400)

| Case / repeat | r4 member ID | Archive term/index → pre-stop applied | Final stop exit | Native result / exit | Native observation seconds | Job |
|---|---|---|---|---|---|---|
| OFFLINE_OLD_CLEAN / 1 | 325443855819284077 | 2/94 → offline | -15 | CATCH_UP_SAME_ID / alive | 0.090891 | [132716923364](https://github.com/alireza-anari/cac-project/actions/runs/43682789400/job/132716923364) |
| OFFLINE_OLD_CLEAN / 2 | 4940938582933845825 | 3/95 → offline | -15 | CATCH_UP_SAME_ID / alive | 0.095607 | [132716923504](https://github.com/alireza-anari/cac-project/actions/runs/43682789400/job/132716923504) |
| PROGRESSED_CURRENT_KILL / 1 | 6686581923474503030 | 2/94 → 115 | -9 | CATCH_UP_SAME_ID / alive | 0.104615 | [132716923533](https://github.com/alireza-anari/cac-project/actions/runs/43682789400/job/132716923533) |
| PROGRESSED_CURRENT_KILL / 2 | 6561955664415336190 | 2/94 → 115 | -9 | CATCH_UP_SAME_ID / alive | 0.090423 | [132716923555](https://github.com/alireza-anari/cac-project/actions/runs/43682789400/job/132716923555) |
| PROGRESSED_OLD_CLEAN / 1 | 2942865035607789468 | 2/94 → 115 | -15 | NATIVE_FAIL_STOP_EXIT2 / 2; 115 > 94 | 0.184042 | [132716923612](https://github.com/alireza-anari/cac-project/actions/runs/43682789400/job/132716923612) |
| PROGRESSED_OLD_CLEAN / 2 | 13438474246869356162 | 2/94 → 115 | -15 | NATIVE_FAIL_STOP_EXIT2 / 2; 115 > 94 | 0.230014 | [132716923485](https://github.com/alireza-anari/cac-project/actions/runs/43682789400/job/132716923485) |
| PROGRESSED_OLD_KILL / 1 | 10424363241616793827 | 3/95 → 116 | -9 | NATIVE_FAIL_STOP_EXIT2 / 2; 116 > 95 | 0.266101 | [132716923527](https://github.com/alireza-anari/cac-project/actions/runs/43682789400/job/132716923527) |
| PROGRESSED_OLD_KILL / 2 | 2767071880837002055 | 2/94 → 115 | -9 | NATIVE_FAIL_STOP_EXIT2 / 2; 115 > 94 | 0.229306 | [132716923505](https://github.com/alireza-anari/cac-project/actions/runs/43682789400/job/132716923505) |

| Case / repeat | PostgreSQL system ID | Pre-grant PID/fullxid → current policy2 PID/fullxid |
|---|---|---|
| OFFLINE_OLD_CLEAN / 1 | 7708271733726511142 | 262/776 → 323/788 |
| OFFLINE_OLD_CLEAN / 2 | 7708271737903542310 | 278/776 → 346/788 |
| PROGRESSED_CURRENT_KILL / 1 | 7708271738161098790 | 245/777 → 337/788 |
| PROGRESSED_CURRENT_KILL / 2 | 7708271730319945766 | 212/776 → 295/788 |
| PROGRESSED_OLD_CLEAN / 1 | 7708271744014819366 | 252/777 → 317/788 |
| PROGRESSED_OLD_CLEAN / 2 | 7708271732822884390 | 229/777 → 305/788 |
| PROGRESSED_OLD_KILL / 1 | 7708271742329942054 | 230/765 → 322/788 |
| PROGRESSED_OLD_KILL / 2 | 7708271735832735782 | 229/776 → 321/788 |

### PR synthetic merge — [run 43682792383](https://github.com/alireza-anari/cac-project/actions/runs/43682792383)

| Case / repeat | r4 member ID | Archive term/index → pre-stop applied | Final stop exit | Native result / exit | Native observation seconds | Job |
|---|---|---|---|---|---|---|
| OFFLINE_OLD_CLEAN / 1 | 3815031877180488493 | 3/95 → offline | -15 | CATCH_UP_SAME_ID / alive | 0.131463 | [132716924955](https://github.com/alireza-anari/cac-project/actions/runs/43682792383/job/132716924955) |
| OFFLINE_OLD_CLEAN / 2 | 6913391784651908454 | 2/94 → offline | -15 | CATCH_UP_SAME_ID / alive | 0.09539 | [132716924972](https://github.com/alireza-anari/cac-project/actions/runs/43682792383/job/132716924972) |
| PROGRESSED_CURRENT_KILL / 1 | 5365832061077746964 | 2/94 → 115 | -9 | CATCH_UP_SAME_ID / alive | 0.138048 | [132716925003](https://github.com/alireza-anari/cac-project/actions/runs/43682792383/job/132716925003) |
| PROGRESSED_CURRENT_KILL / 2 | 5560988339192739901 | 2/94 → 115 | -9 | CATCH_UP_SAME_ID / alive | 0.08528 | [132716924898](https://github.com/alireza-anari/cac-project/actions/runs/43682792383/job/132716924898) |
| PROGRESSED_OLD_CLEAN / 1 | 7478363872845302294 | 2/94 → 115 | -15 | NATIVE_FAIL_STOP_EXIT2 / 2; 115 > 94 | 0.22439 | [132716924750](https://github.com/alireza-anari/cac-project/actions/runs/43682792383/job/132716924750) |
| PROGRESSED_OLD_CLEAN / 2 | 4103151977832885995 | 2/94 → 115 | -15 | NATIVE_FAIL_STOP_EXIT2 / 2; 115 > 94 | 0.216596 | [132716925008](https://github.com/alireza-anari/cac-project/actions/runs/43682792383/job/132716925008) |
| PROGRESSED_OLD_KILL / 1 | 17399862719012954102 | 2/94 → 115 | -9 | NATIVE_FAIL_STOP_EXIT2 / 2; 115 > 94 | 0.216656 | [132716924956](https://github.com/alireza-anari/cac-project/actions/runs/43682792383/job/132716924956) |
| PROGRESSED_OLD_KILL / 2 | 17390643589252643958 | 2/94 → 115 | -9 | NATIVE_FAIL_STOP_EXIT2 / 2; 115 > 94 | 0.185119 | [132716924880](https://github.com/alireza-anari/cac-project/actions/runs/43682792383/job/132716924880) |

| Case / repeat | PostgreSQL system ID | Pre-grant PID/fullxid → current policy2 PID/fullxid |
|---|---|---|
| OFFLINE_OLD_CLEAN / 1 | 7708272250151395366 | 246/777 → 313/788 |
| OFFLINE_OLD_CLEAN / 2 | 7708272079228383270 | 270/776 → 337/788 |
| PROGRESSED_CURRENT_KILL / 1 | 7708272199832096806 | 252/777 → 336/788 |
| PROGRESSED_CURRENT_KILL / 2 | 7708271745239867430 | 221/776 → 305/788 |
| PROGRESSED_OLD_CLEAN / 1 | 7708271729809182758 | 229/776 → 296/788 |
| PROGRESSED_OLD_CLEAN / 2 | 7708271742396616742 | 214/776 → 282/788 |
| PROGRESSED_OLD_KILL / 1 | 7708271743623270438 | 237/777 → 320/788 |
| PROGRESSED_OLD_KILL / 2 | 7708271737634807846 | 230/765 → 322/788 |

In both separate cohorts: offline-old2/2 and current-file-kill2/2 reached current
same-ID state/journal; progressed-old-clean2/2 and progressed-old-kill2/2 panicked.
No native removed-member refusal or timeout occurred in these M cohorts; classifier
branches are not evidence of an executed refusal/timeout. All sixteen retain
one genuine OPEN and zero UNKNOWN during observation, equal complete Root/journal,
all three original current voters, valid old-policy denial and actual policy2
scoped PostgreSQL success/committed-body read before teardown. No new repair ran.
The archived native WAL/snapshot/db inventories and original-majority IDs for each
case are in its full safe `M OBSERVATION` receipt; no copied identifiers across labs.
Elapsed values measure native observation from spawn completion, excluding bootstrap,
archival and the explicit eight-second forced-stop fallback. They are not service SLOs.

Technical verdict: **M_P1_REPRODUCED_WITH_BOUNDED_CAUSE**. Here *bounded cause*
means only the observed immediate native `commitTo` request beyond local lastIndex,
with a matching heartbeat/commitTo stack. It does **not** prove a universal trigger,
leader cached-match mechanism or remediation. P1 remains **OPEN / NOT_FIXED**.
This association is present after both acknowledged clean TERM and forced kill;
current-file kill controls do not show it in this finite matrix.

Independent evidence review covered all eight extracted Push rows and four full
representative GitHub jobs:132716923612,132716923527,132716923364,132716923533.
The reviewer independently checked run/checkout SHA, source-equality step, pinned
binary receipt, one test completion, evidence scan, cleanup and artifact upload.
No blocking inconsistency was found. This review is not an independent rerun and
must not be expanded to all full PR logs or pending regression execution.

## Final-head delivery gate and status matrix

This documentation completion commits no further executable changes. Its final SHA
and synthetic merge cannot be embedded in their own file: the exact final-head
Push/PR/job ledger and completion decision are delivered in
[Issue #49](https://github.com/alireza-anari/cac-project/issues/49) and
[Draft PR #50](https://github.com/alireza-anari/cac-project/pull/50).
**Until final-head workflows, complete fixed cohorts, inherited regressions and
scan receipts are actually verified, final delivery remains INCOMPLETE.**
Canceled/intermediate runs are never substituted for final-head PASS.

| Evidence / result | Status at document freeze | Meaning |
|---|---|---|
| Four distinct M methods, two observations each per code Push/PR cohort | OBSERVED / diagnostic PASS | Four native catch-ups and four P1 panics per cohort; not P1 fixed. |
| Corrected code cohort final workflow/regression jobs | PENDING until external ledger | Sample completion does not prove whole workflow PASS. |
| All prior244 distinct methods | PRESERVED_SOURCE; final execution pending external ledger |169 inherited +H51 +K17 +L7; M adds4 =248 distinct. Scanners/repeats/sensitivity reruns are not extra distinct methods. |
| M test-first absent-driver probe | RED witnessed | Real PG baseline before expected missing-driver assertion. |
| Actual M security assertion failure | NOT_OBSERVED in completed cohorts | No all-scenario security guarantee. |
| Native same-ID recovery P1 | REPRODUCED / OPEN | Commit-index out-of-range native exit2; no fix or accepted workaround. |
| Removed member native refusal / fresh learner repair | Separate preserved L cohort; final execution pending ledger | Not new M results and not repair of M samples. |
| M same-ID auto repair, UNKNOWN reconciliation, new policy/algorithm | NOT_RUN / NOT_IMPLEMENTED | No clearing or successor release from timeout. |
| Historical D rollback | FAIL_SECURITY | Remains unresolved irrespective of green diagnostic CI. |
| Majority rollback / E / Lane3 | OUT_OF_SCOPE / BLOCKED | No extra authorization or evidence. |


## Current status

M_P1_REPRODUCED_WITH_BOUNDED_CAUSE — immediate native out-of-range fail-stop only;
final-head delivery gate still depends on actual external CI ledger, not this label.
P1 stays OPEN. D remains FAIL_SECURITY; Lane3/UNKNOWN reconciliation BLOCKED;
majority rollback/E/shared-custody assumptions unproven; SOURCE-001/GATE-SOURCE
BLOCKED and Gate9/architecture parents OPEN. No Merge or Production approval.
