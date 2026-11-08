# S0-09L literal stale Raft physical replay — execution record

NEW_IMPLEMENTATION_EXPERIMENTAL / NONRESTORED_CURRENT_MAJORITY_ONLY / NO_PRODUCTION.

## Authority and implementation plan

Issue #47 and `docs/architecture/S0_09K_ARCHITECTURE_RULING.md` at management
main `7a2791504a8cfd32ae83e239c51cf28e75611cc7` authorize this bounded experiment.
Technical parent is exact K `9e768a4d1f6c97c429c36475237e132b8e3e7fc2`.
Branch: `work/s0-09l-stale-raft-minority-physical-replay`, Draft stacked against K.

The existing H controller deliberately never imports stale Raft files. L adds an
isolated test-only `h_quorum.l_physical` module; existing H/K/security SQL and tests
remain unchanged. Native etcd is pinned to 3.6.16 with the inherited checksum.

Approach: stop only r4, require positive current r1/r2/r3 membership/status receipts,
produce native `.wal`, `.snap` and `snap/db` by an r4-only low snapshot threshold,
copy the stopped member's full data directory privately and hash every file.
Advance actual Root using K's authenticated policy1→2 transition. Replace only
the stopped r4 data directory with the archived bytes, verify hashes before spawn,
then observe actual same-member Raft catch-up/refusal. No `--force-new-cluster`,
etcdutl logical restore, forged WAL, altered cluster identity, disabled TLS/auth,
concurrent same-ID process or modification of r1/r2/r3 is permitted.

Fresh learner replacement or application-journal replay alone is not L evidence.
The alternative of rewriting snapshot member metadata is rejected because it
would cease to be import of the member's original bytes. Removed-member and
incompatible learner attempts use only stopped/quarantined minority identities;
native diagnostics and actual commands distinguish refusal from unavailable response.

Execution tasks:

- [ ] Write a real healthy baseline plus missing-native-fixture original assertion;
  execute in disposable CI and record the missing-feature RED.
- [ ] Add `h_quorum.l_physical.fixture.Physical` for stopped-copy provenance, native spawn,
  same-ID replay, original-majority invariants and safe native diagnostic receipts.
- [ ] Add focused real tests: policy/pool stale denial plus policy2 positive;
  pre-granted COMMIT with hold; UNKNOWN retained; removed identity and learner
  incompatible-byte cases. No fake outcome from process absence.
- [ ] Run a reasons-specific retirement-authority original assertion mutant on the
  physical-import scenario, exact-byte restoration and identical original GREEN.
- [ ] Run L plus unchanged K17/H51/inherited169, source receipts, independent read-only
  review and final-head push/PR CI; record exact artifacts and Issue #47 handoff.

Review focus: live PID/symlink/path protection; archived native-file identity and
hashes; no current-majority restoration; removal/learner identity mismatch is an
observed native result rather than an assumed rejection; admission never reads
serializable stale minority state as current; UNKNOWN never clears during repair.

## Execution ledger

2026-11-08: live main and K heads matched the authorized SHAs; PR46 Draft/unmerged.
No local Docker executable is installed; real etcd/PG/PgBouncer execution uses
the authorized disposable Actions fixture. Baseline K's final eight workflows
were previously verified complete/success. No claim of local database execution.

Ruling: use inline implementation and one fresh whole-branch read-only reviewer;
the execution authorization supplies the scope and technical constraints. No
additional design/Production approval is inferred. Native replay is a bounded
experiment, not a supported operational restore procedure.

## Results

L_INCOMPLETE — implementation and actual evidence pending. Unsupported majority
rollback, joint old-verifier/root restore, independent custody, E and Lane3 stay
outside scope. Historical D remains FAIL_SECURITY; SOURCE-001/GATE-SOURCE BLOCKED;
Gate9 and architecture parents OPEN. No Merge, APR or Preview modification.
