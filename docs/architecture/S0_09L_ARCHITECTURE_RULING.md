# CAC — S0-09L Architecture Ruling R0: Literal Minority Raft Data Replay

**Date:** 2026-11-09  
**Authority:** Astra Management / Security Architecture  
**Execution:** [S0-09L Issue #47](https://github.com/alireza-anari/cac-project/issues/47)  
**Reviewed technical PR:** [Draft #48](https://github.com/alireza-anari/cac-project/pull/48), exact final HEAD `ba5bc82170da4523b39b1512eb7d2de344255c3a` on `work/s0-09l-stale-raft-minority-physical-replay`; base `work/s0-09k-policy-retirement-experiment` at `9e768a4d1f6c97c429c36475237e132b8e3e7fc2`. **OPEN/DRAFT/UNMERGED.**  
**Handoff:** [S0-09L technical report](https://github.com/alireza-anari/cac-project/blob/ba5bc82170da4523b39b1512eb7d2de344255c3a/docs/security/S0_09L_LITERAL_STALE_RAFT_PHYSICAL_REPLAY_HANDOFF.md), [final Issue #47 receipt](https://github.com/alireza-anari/cac-project/issues/47#issuecomment-6726703957).  
**Formal Management vote:** `L_STALE_RAFT_MINORITY_CURRENT_Q_BOUNDED_PASS / NATIVE_SAME_ID_AVAILABILITY_P1_OPEN / NO_SAME_ID_RESTORE_APPROVAL / NO_MERGE_OR_PRODUCTION`.  
**Classification:** `CAC-NEW-ORIGIN-S0-07 / NEW_IMPLEMENTATION_EXPERIMENTAL / PROTOCOL_PROPOSED`.

## 1. Verification: scope and genuinely executed evidence

Management verified PR #48 exact head and base SHA, **eight changed files only** (seven L experimental/report paths and one scoped CI workflow), without modifying parent H/K/core SQL/Preview/APRs. Read the exact `l_physical/fixture.py`, seven source test methods `test_00` through `test_06`, sensitivity source and technical report; reviewed original final-run GitHub Actions job logs for L proof, sensitivity and D's historical negative. Management did **not** rerun etcd/PG locally or inspect raw private WAL bytes. A role-separated independent reviewer compared **12 archived/reimported native file paths/size/SHA-256** and selected receipts; this is **not** an independent physical-host, custody or external certification.

**Nine exact-head GitHub Actions workflows `completed/success`:**

| Suite | Final run | Bounded observed evidence |
|---|---|---|
| L push | [42517943171](https://github.com/alireza-anari/cac-project/actions/runs/42517943171) | L7 + K17/H51, real native physical test/sensitivity |
| L PR | [42517949002](https://github.com/alireza-anari/cac-project/actions/runs/42517949002) | L7 + K17/H51, selected proof+sensitivity log independently inspected |
| H PR | [42517948872](https://github.com/alireza-anari/cac-project/actions/runs/42517948872) | Preserved H51 |
| K PR | [42517948857](https://github.com/alireza-anari/cac-project/actions/runs/42517948857) | Preserved K17 |
| Backend | [42517948890](https://github.com/alireza-anari/cac-project/actions/runs/42517948890) | Inherited 94 |
| C | [42517948939](https://github.com/alireza-anari/cac-project/actions/runs/42517948939) | Inherited 20 |
| D | [42517948745](https://github.com/alireza-anari/cac-project/actions/runs/42517948745) | Inherited 15 plus intentionally failing legacy C-anchor rollback probe |
| F | [42517948703](https://github.com/alireza-anari/cac-project/actions/runs/42517948703) | Inherited 40 with F's original assumed-W limits |
| Focused B | [42517948873](https://github.com/alireza-anari/cac-project/actions/runs/42517948873) | Supplemental repeated coverage, not a new case cohort |

**Distinct inventory: L7 + K17 + H51 + inherited169 = 244 distinct case methods across separate workflows**, not one combined job; repeats, RED/GREEN probes and two scanner methods do not increase this count. Exact final PR L proof job `128844979431` and sensitivity job `128844979310` each recorded `Ran 7 tests ... OK`. Mutated non-controller retirement assertion original RED, exact implementation restored, same original GREEN; no muted guard accepted. D final job `128844978263` retained `Rolled-back anchor revived previous-owner authority` and `S009D SECURITY FAIL/BLOCKED` despite overall workflow `success`. **Original D remains `FAIL_SECURITY`.**

## 2. Observed native physical operations — three different outcomes

**Authentic physical state:** A fully stopped r4 minority member's actual `member/wal/*.wal`, `member/snap/*.snap` and `member/snap/db` with pre-cut per-file inventory was archived and copied back byte-for-byte (not logical etcdutl export or fake app journal). The three original surviving voter processes r1/r2/r3 remained current and nonrestored, with matched current Root policy/revision/head/journal. A real five-etcd-member, three-PG-cluster, PgBouncer lab ran on **one CI host/admin domain** using etcd3.6.16, PG17.11, PgBouncer1.22.0, Python3.12.15.

- **Native same-ID catch-up observed for one real stopped-byte replay:** the originally archived r4 ID reached the newer current policy2/revision/head and complete ordered journal, with real old readiness/issuer/SQL denial and healthy current policy2 SQL. This is only an *observed* positive case, **not a general same-ID restore guarantee**.
- **Native refusal observed:** removed old r4 member data and separately incompatible old bytes presented under a fresh learner configuration were actually refused with old on-disk identities/exit1, followed where appropriate by correctly enrolled fresh learner catch-up. Native refusal is distinct from catch-up or claimed global fail-closed.
- **P1 **availability** still OPEN:** when r4 had progressed after the archived snapshot and the real forced stop/SIGKILL path restored the older bytes, native Raft emitted `tocommit(1276) is out of range [lastIndex(1271)]` in the PR L sensitivity job and `tocommit(3015) ... [lastIndex(3010)]` in PR proof, and exited with **code 2**. Earlier L source expected catch-up and failed; the final L06 contract correctly recognizes **`native_raft_fail_stop` as a failure of same-ID recovery**, not a successful repair or healthy member. Around the failure, majority Root state/three original members remained current, old-policy admission denied and **real healthy policy2 PostgreSQL SQL succeeded before any repair**. Only after that observation did separately consensual member removal plus a **fresh new-ID learner** recover cluster membership. No claim of upstream etcd fix or proven root cause from the panic text alone.

**OPEN and UNKNOWN:** L01 observed old legitimate grant and real protected COMMIT with successor hold until a known-authoritative CLOSE; L02 kept UNKNOWN unresolved through actual native replay/repair. **No UNKNOWN, orphan obligation or privilege could be cleared on timeout, member absence, cancellation or a new learner.** Healthy path was verified after each allowed refusal/catch-up.

## 3. Evidence boundaries and explicit NOT_RUN

The accepted result is a **bounded observational safety claim under current nonrestored 3/5 R majority and a surviving trusted, mandatory current guard/SQL/PG path**, not a proof of unconditional recovery. In particular:

- An **available, actually stale serializable minority response** routed into the critical authority admission decision was **NOT_RUN**. Stopped endpoint unavailable and post-native-catch-up current responses are not the same threat. Native packet-level ACK-loss, arbitrary live-writer/torn WAL and all snapshot/compaction/crash windows also NOT_RUN.
- A coherently restored **R majority**, jointly restored obsolete verifier/root and other shared physical/key/admin/custody failures remain **UNSUPPORTED / SECURITY_UNPROVEN / NOT_RUN**. If all roots/guards rewind, `GLOBAL_FAIL_CLOSED_NOT_ESTABLISHED`.
- G1–G5 of independent E remain P0 `DESIGN_BLOCKED`, no qualified E1/E2.
- Same-ID stale recovery **NOT_QUALIFIED** as reliable or approved operational procedure. Native panic/exit2 has a separate **P1** tracking action [S0-09M Issue #49](https://github.com/alireza-anari/cac-project/issues/49); a green CI may legitimately assert a specific fail-stop but must not count the failed recovery as availability PASS.
- True Lane3 orphan `OPEN_UNKNOWN/FENCED_UNRESOLVED` resolution **P0 BLOCKED**, possibly indefinite safe downtime; historic S0-09D C-only rollback **`FAIL_SECURITY`**. 
- [SOURCE-001 #1](https://github.com/alireza-anari/cac-project/issues/1)/GATE-SOURCE **BLOCKED**, [canonical architecture Gate #9](https://github.com/alireza-anari/cac-project/issues/9) and parents [#33](https://github.com/alireza-anari/cac-project/issues/33), [#28](https://github.com/alireza-anari/cac-project/issues/28), [#23](https://github.com/alireza-anari/cac-project/issues/23) remain OPEN. No actual source v3.37-v3.39 recovery, Production, accepted root/recovery protocol, full Product integration, APR or Sprint0 acceptance.
- Preview V0 [Draft PR #44](https://github.com/alireza-anari/cac-project/pull/44) and prior experiments including K #46 remain independent, unmerged and untouched. No Merge authorized.

## 4. Management disposition and next measured slice

**Accept `L_STALE_RAFT_MINORITY_CURRENT_Q_BOUNDED_PASS` only for observed native minority physical import/rejection/catch-up plus real guard and healthy SQL behavior; attach the still-open P1 native recovery fail-stop.** [Issue #47](https://github.com/alireza-anari/cac-project/issues/47) may close **only as completion of its bounded physical-replay experiment**, not as a sign-off of reliable same-ID restarts. Keep PR #48 OPEN/DRAFT/UNMERGED. Do not silently rewrite/erase its earlier failed CI history or native panic; preserve the external final-head receipt that completes the handoff's stated conditional gate.

**Next separately authorized work:** [S0-09M Issue #49](https://github.com/alireza-anari/cac-project/issues/49), one bounded **P1 availability triage** using existing disposable stopped-native-byte fixture to characterize real exit2 preconditions, source/incident evidence and safe fallback under surviving current quorum — no modification of etcd, no bypass of security guard, no claim of safe same-ID recovery, no automatic Production procedure. Delivery as a new isolated experimental Draft PR from exact #48 head and fresh final CI/source review. A security gate anomaly immediately escalates to P0, superseding P1 triage. An available stale-response admission test remains an independent **P0 NOT_RUN** obligation that requires its own authorization later.

**Formal final vote:** `ACCEPT_L_BOUNDED_CURRENT_Q_PHYSICAL_EVIDENCE / P1_NATIVE_REPLAY_AVAILABILITY_OPEN / M_DIAGNOSTIC_ONLY_AUTHORIZED / GATES_AND_PRODUCTION_UNCHANGED`.
