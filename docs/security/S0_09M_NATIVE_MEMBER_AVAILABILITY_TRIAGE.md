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
Corrections are M-only. Final execution/log review remains pending.

## Current status

M_P1_DIAGNOSIS_INCONCLUSIVE — M implementation/execution evidence pending.
P1 stays OPEN. D remains FAIL_SECURITY; Lane3/UNKNOWN reconciliation BLOCKED;
majority rollback/E/shared-custody assumptions unproven; SOURCE-001/GATE-SOURCE
BLOCKED and Gate9/architecture parents OPEN. No Merge or Production approval.
