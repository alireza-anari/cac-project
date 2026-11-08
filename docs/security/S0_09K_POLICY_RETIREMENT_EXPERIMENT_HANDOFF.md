# S0-09K — bounded real Root policy retirement evidence

Status: NEW_IMPLEMENTATION_EXPERIMENTAL / PROTOCOL_PROPOSED / NO_PRODUCTION.

## Scope and provenance

Execution authority is Issue [#45](https://github.com/alireza-anari/cac-project/issues/45)
and `docs/management/CAC_POST_PREVIEW_ENGINEERING_RESUMPTION_R0.md` at main
`1567a68a0a27b17412922e725bca960ff42d30ad`. This branch starts exactly at
H head `b32416c799160f0e5957506d58254a693cbc231f`, rather than main. Delivery is
Draft [PR #46](https://github.com/alireza-anari/cac-project/pull/46), branch
`work/s0-09k-policy-retirement-experiment`, stacked against
`work/s0-09h-quorum-survival-poc`. No earlier PR is merged, cherry-picked or edited.

Test-first checkpoint: `15c155f61314c401c6f7556c24f9ddbec1e087d1`.
Implementation checkpoint: `a76bbb833a54bc47cd6cee7b79784f7ef9f5815f`.
Final document commit and its exact-head CI receipts are recorded externally in
PR #46 / Issue #45, avoiding a self-referential commit hash in this file.

## What changes

The authenticated control role alone can commit `retire_policy(expected=1,new=2,
request=<canonical UUID>)`. The existing real etcd CAS writes policy generation,
profile identifier, retirement cut, request receipt, full operation state and ordered
journal/head together. Signer generation stays **1**. This tests retirement of
the admitted **policy generation**, rather than signer rotation or a static mismatch.
The two profile names are bounded generation labels; this experiment does not
implement or qualify arbitrary semantic changes in authorization algorithms.

Only 1→2 is supported. Invalid roles/types, stale/new duplicate requests, rollback
and generation 3 are denied. An exact retry reads the original committed request
receipt and revision without creating another transition. Concurrent contenders
use the existing head CAS; only one distinct request can commit the cut.

New ADMIT and FIRST_USE require the current generation. Old active-readiness
proofs and delayed old replies are denied even with a valid signature under the
still-current signer. Existing exact operations granted before the retirement
sequence may continue under their original binding. This exception requires
an OPEN granted operation, exact ticket/actor/epoch/binding and an ordered
pre-cut FIRST_USE; it does not admit new old-policy work.

An unresolved retired OPEN or UNKNOWN blocks new admission and SQL-config
adoption. The private SQL policy remains 1 while such holds exist, allowing the
exact pre-granted transaction to reach a definite result through unchanged SQL
checks. Current R denies new policy1 readiness. The existing trusted lab
controller may adopt config2 only after a full current R read, unchanged catalog
measurement, private ACL validation and absence of retired unresolved operations.
The runtime and issuer cannot update that private config. There is no SQL
predicate relaxation, user-settable policy override or LOGIN bypass.

Known COMMIT/ABORT can close the exact original operation. UNKNOWN cannot be
cleared, including after cancellation or missing first-use acknowledgment.
Fresh fixture namespaces isolate tests; they are not a recovery procedure for
an orphan operation or permission to discard a committed journal.

## Proof topology and trust boundary

Actual Actions runners start five etcd voting processes with durable local data
directories, TLS-authenticated root transport, three independent PostgreSQL
containers (A, restored B and anchor C), and real transaction-pooling PgBouncer.
They are independent database clusters/processes **on one disposable CI host**,
not independent administrators, failure domains, hardware roots or data centers.

Pinned fixture versions: etcd **3.6.16** (upstream archive checksum checked),
PostgreSQL **17.11** (inherited pinned image digest), PgBouncer
**1.22.0-1build4**, Python **3.12.15**. Source: the new
`.github/workflows/policy-retirement.yml`, inheriting H's actual fixtures.
The proof logs record member/cluster IDs, term/index, policy commit revision,
PostgreSQL system identifiers and observed pool PID/transaction IDs.

This is conditional on a current, non-restored majority, current mandatory guard,
trusted control/controller/observer and protected configuration. Existing shared
lab administrators and signing-key custody remain inherited assumptions. No
responsive restored majority, joint old-verifier/root restore, literal stale Raft
WAL/snapshot import, physical clone or real custody independence is qualified.

## New test inventory

Each row names one method in `h_quorum/tests/test_policy_retirement.py`; all use
the actual integration fixture. Repeated lanes and mutations are not new tests.

| ID | Executed assertion / healthy control | Result |
|---|---|---|
| K00 | Guarded policy1 baseline; real atomic policy2 cut, signer1 unchanged, operations preserved, journal/state same revision | PASS (PR sensitivity job 128631884156) |
| K01 | Stale-policy SQL readiness and old new-ADMIT denied; supplemental no-ticket RLS denial (not alone retirement-discriminating); policy2 scoped RLS succeeds | PASS (PR sensitivity job 128631884156) |
| K02 | Non-control role cannot retire; control retirement and policy2 RLS succeed | PASS (PR sensitivity job 128631884156) |
| K03 | Invalid/backward/future mutations denied; exact receipt replay is idempotent | PASS (PR sensitivity job 128631884156) |
| K04 | Concurrent distinct control requests produce exactly one committed cut | PASS (PR sensitivity job 128631884156) |
| K05 | Old active transcript has valid HMAC under signer1 but guard/verification/replay denied at policy2; current proof succeeds | PASS (PR sensitivity job 128631884156) |
| K06 | Real protected old-policy UPDATE/COMMIT survives; successor blocked before and after local COMMIT until authoritative CLOSE; restored B policy2 succeeds | PASS (PR sensitivity job 128631884156) |
| K07 | Known abort closes the original old-policy operation; new policy2 work succeeds | PASS (PR sensitivity job 128631884156) |
| K08 | Cut after durable OPEN but before FIRST_USE denies use; UNKNOWN retained; no CLOSE, adoption or successor | PASS (PR sensitivity job 128631884156) |
| K09 | Actual committed retirement TLS ACK dropped; exact request resolves once against current R; policy2 positive | PASS (PR sensitivity job 128631884156) |
| K10 | Cut after old readiness/binding read but before ADMIT creates no OPEN; policy2 positive | PASS (PR sensitivity job 128631884156) |
| K11 | Real PgBouncer same backend PID/new xid; persistent old context denied; current policy2 scoped SQL succeeds | PASS (PR sensitivity job 128631884156) |
| K12 | Actual old SQL overlay rejected by catalog admission; quarantined issuer/runtime stay NOLOGIN at Root2 | PASS (PR sensitivity job 128631884156) |
| K13 | Actual PostgreSQL sleep/cancel after cut; backend reused, UNKNOWN retained, adoption denied | PASS (PR sensitivity job 128631884156) |
| K14 | Stop r4/r5; commit policy2 and actual guarded SQL with original r1/r2/r3; restart minority using same directories | PASS (PR sensitivity job 128631884156) |
| K15 | Same issuer SQL connection ready before cut and not ready after; old issuer ADMIT denied; current issuance and RLS succeed | PASS (PR sensitivity job 128631884156) |
| K16 | Runtime and issuer SQL roles cannot downgrade private config; authorized policy2 remains healthy | PASS (PR sensitivity job 128631884156) |

K14 is minority outage, not minority snapshot restore. K12 exercises loaded
old SQL/catalog quarantine, not privileged execution of a jointly restored root
and verifier. The pre-cut continuation is deliberate preservation of already
granted authority, not permission to create new retired-policy authority.

## RED / restoration / GREEN

### Missing-feature RED

At test-first SHA `15c155f61314c401c6f7556c24f9ddbec1e087d1`, real five-voter R
and healthy policy1 guarded SQL preceded the original assertion:
`Actual Root policy retirement transaction is not implemented`.
Push [42447701108](https://github.com/alireza-anari/cac-project/actions/runs/42447701108)
and PR [42447704188](https://github.com/alireza-anari/cac-project/actions/runs/42447704188)
failed with one original test failure and exit 1. This is a missing-feature
baseline, not a demonstrated old-owner exploit and not the sensitivity mutant.

### Retirement-authority sensitivity

`python -m h_quorum.policy_sensitivity` first runs the healthy original K02.
It temporarily removes only the control-role check in `retirement.py`, restarts
the real service through the inherited harness and reruns the identical assertion.
Required RED is an actual authenticated coordinator committing policy2 followed
by `Policy retirement accepted a non-control role`, exit 1 and exactly one
assertion failure, with no fixture error. A finally block restores exact source
bytes and SHA-256; restart must preserve the mutant namespace state/revision.
The same original test then runs GREEN in a fresh synthetic namespace. No real
R rollback, old-namespace erasure or timeout-based UNKNOWN clearing is performed.
The full K17 suite subsequently runs against restored source.

Observed **PASS** in PR sensitivity job
[128631884156](https://github.com/alireza-anari/cac-project/actions/runs/42448312489/job/128631884156)
at implementation SHA `a76bbb833a54bc47cd6cee7b79784f7ef9f5815f`:
healthy K02 (10.702s), deliberate role-check mutant RED (one assertion failure,
1.911s), identical restored K02 GREEN (10.207s), then K17 GREEN (17 tests,
243.892s). Restored `retirement.py` SHA-256:
`c619aa3043e1342d97c50b814e14c95b98a586688442cb43b27c0668d4d29652`.
The committed mutant namespace remained at policy2/revision15 across restart.

Representative real receipts from that PR job (different runs have different IDs):

- A/B/C PostgreSQL system IDs: `7705658191059337254`,
  `7705658193085710375`, `7705658196602347559`.
- R cluster ID `17171306114936220099`, five voters, term2; K00 observed
  policy1 revision28/index82, then policy2 revision35/index99, signer1 unchanged.
  Full operation journal/head had the same committed MVCC revision35.
- Original survivors in K14: r1 `16004560072492759740`, r2
  `2458226335158552760`, r3 `11219762908116454195`; r4/r5 were stopped.
- K11 PgBouncer backend PID **1068**, old xid **1084**, new xid **1092**;
  retained old context denied, new policy2 scoped SQL positive.
- PR checkout log: synthetic merge `a6f2e7c`, exact PR_HEAD `a76bbb833a54bc47cd6cee7b79784f7ef9f5815f`,
  H base `b32416c799160f0e5957506d58254a693cbc231f`; required source-equality step passed.


## Regression and CI provenance

H's 51 distinct tests and the inherited 169 distinct tests are preserved byte
for byte. K adds 17 distinct real integration methods: **237** total distinct
inherited+H+K methods observed across completed implementation-checkpoint suites.
The historical D safety-failure probe is additional and remains FAIL_SECURITY. Repeated proof,
sensitivity, push and PR executions do not increase this count. Scanner tests
and repeated supplemental B/C suites are accounted separately.

K push and PR workflows run unchanged H51 in the proof lane, K17 in both lanes,
and authority sensitivity in its own lane. Existing PR workflows run H51 plus
H's existing sensitivities and inherited full-backend94/C20/D15/F40 (169).
The existing inherited workflows are not advertised as K-branch push runs.
PR checkout is GitHub's synthetic merge; the K receipt records both tested
merge SHA and PR head and requires identical backend/new-workflow source trees.

Implementation-checkpoint receipts (`a76bbb833a54bc47cd6cee7b79784f7ef9f5815f`):

| Workflow / commands | Receipt | Observed result |
|---|---|---|
| Full Backend: inherited43, trusted24, process/pool27, original sensitivity and rollback/reapply commands | [42448312299](https://github.com/alireza-anari/cac-project/actions/runs/42448312299), job128631883585 | PASS, command exits 0; 94 distinct, repeated suites before/after restoration |
| C20 plus migration down/up/ACL/bootstrap checks | [42448312348](https://github.com/alireza-anari/cac-project/actions/runs/42448312348), job128631883707 | PASS, 20 before/after; exits 0 |
| D phase1 3 + phase2 4 + phase3 8, original expected historical rollback failure and restoration | [42448312320](https://github.com/alireza-anari/cac-project/actions/runs/42448312320), job128631883605 | 15 bounded cases and restoration PASS; historic safety assertion **FAIL_SECURITY**, harness explicitly records expected RED |
| F40 and original sensitivity/restoration | [42448312407](https://github.com/alireza-anari/cac-project/actions/runs/42448312407), job128631883911 | PASS, 40 before/after, exits 0; still assumed-W scope |
| `python -m h_quorum.run` | [42448312258](https://github.com/alireza-anari/cac-project/actions/runs/42448312258/job/128631978810), proof job128631978810 | PASS, 51 tests/867.984s, no skips, exit 0 |
| `python -m h_quorum.policy_sensitivity`; `python -m h_quorum.policy_run` | [42448312489](https://github.com/alireza-anari/cac-project/actions/runs/42448312489/job/128631884156), sensitivity job128631884156 | PASS; reason-specific mutant child exit1 is required; healthy/restored probes and K17 exit0 |
| Additional focused B | [42448312278](https://github.com/alireza-anari/cac-project/actions/runs/42448312278) | PASS; supplemental repeated coverage, not additional distinct inventory |

Historical D log at 04:52:30 UTC retains the actual original failure:
`AssertionError: True is not false : Rolled-back anchor revived previous-owner authority`,
then `FAILED (failures=1)` and `S009D SECURITY FAIL/BLOCKED anchor rollback`.
The passing D workflow records this failure; it does not turn its security result green.

Final documentation-head push/PR receipt and tested synthetic merge are supplied
in the external Issue #45 / PR #46 delivery ledger after they complete; this
report does not predict their result. Both SHA and workflow IDs must be checked
there before treating the final regression gate as satisfied. Artifacts use `s009k-<run>-<attempt>-<lane>`; their internal
`evidence-s009h/` directory deliberately retains the inherited safe scanner
allowlist. No private bootstrap files are deliverable artifacts. This workspace
has no Docker daemon; actual DB/consensus execution is on disposable Actions
runners, not claimed as a local run.

## Independent source review

A separate read-only reviewer inspected exact parent→candidate source, original
assertions and the control restoration path. No P0/P1 authorization bypass was
identified in that source review. One P2 was identified before implementation
commit: an issuer SQL call without a ticket could fail independently of policy
retirement. K15 was corrected to test readiness on the **same actual issuer
connection before and after the cut**, retaining a valid bound old-policy ADMIT
negative and actual current-policy issuance/RLS positive. The reviewer confirmed
the correction at `a76bbb833a54bc47cd6cee7b79784f7ef9f5815f`.

Source review is neither an external certification nor a substitute for the CI
results. The same reviewer independently read the selected actual completed PR sensitivity
job log and checkout/source-provenance receipt. It confirmed the reasons-specific
coordinator commit RED, matching source restoration SHA, retained real R state,
same original GREEN, K17 completion and paired positive controls. No P0/P1 was
identified in those selected logs. A second minor reporting correction separates
K01's policy-discriminating readiness assertion from supplemental no-ticket RLS
denial, which alone would fail before retirement too. The reviewer did not execute
tests or access private bootstrap fixtures. Its evidence review covers selected
completed logs, not every line of every workflow or external certification.

## Residual findings and untested scope

| Severity | Finding / trust assumption | State / consequence |
|---|---|---|
| P0 | Restored responsive majority plus old verifier remains indistinguishable without an independent qualified continuity root | Outside scope; GLOBAL_FAIL_CLOSED_NOT_ESTABLISHED |
| P0 | Root E G1–G5 and historical D C-only rollback are not repaired | DESIGN_BLOCKED; D remains FAIL_SECURITY |
| P0 | Unknown local outcome cannot be reconciled by timeout, process absence or operator signature | Lane3/OPEN_UNKNOWN recovery BLOCKED; potentially indefinite outage |
| P1 | Current guard/catalog pins, control role, observer and private SQL controller must stay trusted | Privileged/common-admin bypass NOT_RUN; no custody independence claim |
| P1 | Profiles are generation labels, not arbitrary semantic policy rewrites | Only 1→2 admission retirement is covered; generation3/algorithm migration NOT_RUN |
| P1 | Fresh K genesis adds policy fields | Existing pre-K H namespace upgrade/migration NOT_DEMONSTRATED; no deployed namespace compatibility claim |
| P1 | Five processes and three databases share a CI host and administrator | Independent infrastructure/HA/disaster recovery NOT_RUN |
| P1 | Retirement blocks fresh admission while old holds remain | Deliberately conservative availability; no unsafe successor or orphan release |
| P2 | Exact manifest/ACL pins and profile metadata require controlled future changes | No canonical architecture/APR approval inferred |
| P2 | Issuer negative originally lacked retirement discrimination | Corrected before candidate commit; independently checked |

All SQL, existing H tests, other backend trees, Preview and canonical architecture
documents remain unchanged. Workflow source receipts enforce relevant inherited
tree equality. Migration behavior is inherited rather than a new migration:
unchanged H regression exercises its original rollback/reapply and ACL/catalog
gates; K12 adds old-overlay rejection under current policy2. No new SQL migration
or existing-namespace upgrade is claimed.

## Architecture recommendation

The implementation-checkpoint evidence supports the narrow policy-generation
retirement slice. Recommend `K_POLICY_RETIREMENT_REAL_Q_SURVIVAL_EVIDENCE_PASS`
**only after** final-head push/PR and synthetic-merge receipts in the delivery
ledger are successful; until that gate it is `K_INCOMPLETE`. This establishes only the tested
policy-generation retirement under a current surviving R majority and current
mandatory guard. Management alone interprets acceptance. SOURCE-001/GATE-SOURCE
remain BLOCKED; Gate #9 and parent architecture issues remain OPEN. Lane3 remains
BLOCKED. No Production deployment, accepted source baseline, protocol approval,
Sprint 0 completion or general rollback security follows from this experiment.
