# CAC — S0-09N Architecture Ruling R0: Fresh-Identity Learner Repair After Native Same-ID Fail-Stop

**Date:** 2026-11-15  
**Authority:** Astra Management / Security Architecture  
**Execution:** [S0-09N Issue #51](https://github.com/alireza-anari/cac-project/issues/51)  
**Parent P1:** [S0-09M Issue #49](https://github.com/alireza-anari/cac-project/issues/49)  
**Reviewed diagnostic:** [S0-09M Draft PR #50](https://github.com/alireza-anari/cac-project/pull/50), exact head `f679274a4ff5ff32978d9c87362a5e4e1c8f548c`.  
**Physical replay foundation:** [S0-09L Draft PR #48](https://github.com/alireza-anari/cac-project/pull/48), exact head `ba5bc82170da4523b39b1512eb7d2de344255c3`.  
**Formal vote:** `AUTHORIZE_S0_09N_FRESH_ID_LEARNER_REPAIR_QUALIFICATION / P1_MITIGATION_NOT_YET_ACCEPTED / CURRENT_NONRESTORED_QUORUM_ONLY / NO_MERGE_OR_PRODUCTION`.  
**Classification:** `CAC-NEW-ORIGIN-S0-07 / NEW_IMPLEMENTATION_EXPERIMENTAL / PROTOCOL_PROPOSED`.

## 1. Evidence that motivates this ruling

S0-09M's final exact-head Push and PR cohorts directly observed the same bounded pattern: after progress beyond an older native archive, restoring the older WAL/snapshot/db under the same member identity can make etcd/Raft panic with a commit index beyond the local last index and exit 2. The same matrix's offline-old and progressed-current-file controls caught up. The diagnosis is finite and pinned to etcd 3.6.16 in a single-host disposable lab; it is not a universal trigger or a demonstrated Raft root cause.

The L06 experiment separately observed a fresh-identity learner replacement after an actual native fail-stop, with the original current quorum preserved and healthy current-policy SQL checked before repair. L01 and L02 separately demonstrate pre-granted OPEN and genuine UNKNOWN preservation through other replay paths. **No existing cohort combines the exact M panic, fresh-identity replacement, and both operation-hold cases in one bounded acceptance slice.** Therefore the P1 mitigation is plausible but not yet qualified as a coherent operational workaround.

S0-09M final delivery was accepted as a bounded diagnostic. Issue #49 remains OPEN and the same-ID path remains NOT QUALIFIED.

## 2. Architecture decision

Authorize exactly one finite P1 mitigation-qualification slice: quarantine the failed old member and replace it with a new etcd member identity through the surviving current quorum, using a fresh empty data directory and etcd's learner mechanism.

The candidate sequence follows the existing L `Cluster.replace()` implementation and the official etcd 3.6 replacement/learner model:

1. Prove the original current nonrestored quorum, current cluster ID, current Root state/revision/journal and mandatory trusted guard remain valid. Abort without membership change on ambiguity or inconsistency.
2. Prove the old member process is absent; retain its old native files in private quarantine for forensics. Never restart or reuse those old bytes under the old ID.
3. Commit removal of the exact failed old member ID through the authenticated current quorum; verify authoritative membership no longer contains it.
4. Add exactly one fresh learner with a new unique identity, new peer identity/certificate and empty data directory; start against the current membership with `initial-cluster-state=existing`.
5. Keep it non-voting until authenticated status and current Raft-log catch-up are verified.
6. Explicitly promote only after etcd accepts promotion; verify fresh ID, voter membership, unchanged cluster ID and unchanged original current voters.
7. Preserve Root/journal and application operation semantics. An OPEN remains held until actual local outcome/ACK and authoritative CLOSE. An UNKNOWN stays UNKNOWN and blocks successor/adoption; no timeout, member replacement or promotion resolves it.
8. Verify old-policy denial and healthy current-policy SQL where state permits. UNKNOWN is intentionally fail-closed; do not force adoption merely to produce a positive SQL result.

The etcd v3.6 runtime reconfiguration guide requires a functioning majority for membership changes, says changes must be sequential, and documents learner catch-up before explicit promotion. Its data-corruption guide documents replacement of a corrupted member. These upstream contracts support the protocol shape, but do not themselves qualify CAC's combined authority/operation invariants.

## 3. Frozen execution authorization

Issue #51 authorizes two distinct scenarios, two repetitions per case per Push and PR trigger, each in a fresh disposable five-voter/three-PostgreSQL lab:

- `N_PROGRESS_OLD_CLEAN_OPEN`: reproduce the exact M old-byte native panic after clean SIGTERM; carry a genuine pre-granted OPEN through removal, fresh learner catch-up and promotion; keep successors blocked until actual COMMIT ACK and authoritative CLOSE.
- `N_PROGRESS_OLD_KILL_UNKNOWN`: reproduce the exact M old-byte native panic after SIGSTOP/non-child SIGKILL; carry a genuine UNKNOWN through replacement; keep it unresolved and keep successors/adoption denied.

Eight observations total across the two CI triggers. No outcome-driven reruns, matrix expansion or fabricated outcomes. If the exact native panic precondition does not reproduce, mark `N_PRECONDITION_NOT_REPRODUCED`; do not claim mitigation PASS.

Required evidence includes actual old/new member IDs, process-stop proof, file hashes, exact native exit2/panic, three original current-voter identities and Root/journal equality at each boundary, consensus-committed membership operations, learner non-voting/catch-up/promotion receipts, OPEN/UNKNOWN invariants, policy denial, SQL evidence where permitted, safe artifact scanning, exact-head Push/PR CI and role-separated source/log review.

## 4. Change boundary and prohibited actions

New branch `work/s0-09n-fresh-identity-repair-qualification` must start from exact M head `f679274a4ff5ff32978d9c87362a5e4e1c8f548c`, with a new Draft PR stacked on #50.

Allowed changes are limited to new `experimental/backend/h_quorum/l_physical/n_*` files, one scoped N workflow if needed, and `docs/security/S0_09N_FRESH_IDENTITY_REPAIR_QUALIFICATION.md`.

Do not change M/L parent code, H/K inherited assertions, Raft/etcd binaries, Root/security guards, SQL, Preview, canonical APRs or architecture baseline. No same-ID replay retry, old WAL reuse, force-new-cluster, whole-cluster restore, strict-reconfiguration bypass, automatic UNKNOWN clearing, quorum reduction, Production/customer data, Merge or production runbook acceptance.

## 5. Acceptance and residual gates

Accept `N_FRESH_ID_LEARNER_REPAIR_BOUNDED_PASS` only if the exact M fail-stop precondition is observed and both OPEN and UNKNOWN invariants survive the complete fresh-identity replacement path under the stated disposable current-quorum envelope. Native panic is not itself a successful recovery; the recovery is only the fresh-identity path.

Any current Root/majority/admission/SQL/OPEN/UNKNOWN invariant violation is `N_SUPPORTED_SECURITY_FAIL`, supersedes P1 and escalates to P0. A timeout or untyped error is inconclusive, never permission to promote, clear or retry.

Issue #49 stays OPEN until independent review and Management acceptance of a bounded mitigation. Even a successful N result is not Production authorization and does not establish coherently restored-majority protection, global fail-closed behavior, independent custody, or Lane3 orphan resolution.

Unchanged gates: S0-09D `FAIL_SECURITY`; E G1–G5 P0 DESIGN_BLOCKED; Lane3 OPEN_UNKNOWN clearing BLOCKED; restored-majority/old-verifier and independent custody unsupported; SOURCE-001/GATE-SOURCE blocked; Gate #9 and architecture parents #23/#28/#33 open. All experimental PRs remain Draft/unmerged; no canonical source, Sprint0, Product/Production or Merge acceptance follows.
