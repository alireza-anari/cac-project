# S0-09H execution checkpoints

`Q_SURVIVAL_ONLY / NONRESTORED_MAJORITY_REQUIRED / SECURITY_UNPROVEN / PROTOCOL_PROPOSED`

This is an intermediate execution record, **not the final security handoff or completion of H-01–H-06**. Issue31 and management authorization at main913b6ea0f12cd23d4ce8848e3cb38c6b4c99ed85 govern. Parent Draft27/head2bebe0022956809b3842a015d215e6332c5a8b0f verified; independent architecture review30/6608a644b20dc091fe38137e1bd593c676c188c2 read, not merged. Draft32 targets `work/s0-09f-w-oracle-deny-only-poc`; branch `work/s0-09h-quorum-survival-poc`.

## Stage1 observed source checkpoint

Source9268aa4c6821efd48cc0b1a877caca7de6eeb0db:

| Evidence | Actual outcome |
|---|---|
| [H Push42245461841](https://github.com/alireza-anari/cac-project/actions/runs/42245461841) | OBSERVED_PASS7 distinct root/transport preflight cases; no skips |
| [H PR42245474286](https://github.com/alireza-anari/cac-project/actions/runs/42245474286) | OBSERVED_PASS7; tested synthetic merge d49c66f507415eb8bb0f838068fcc507cbc7c7bb; head9268aa4c6821efd48cc0b1a877caca7de6eeb0db; workflow checks head-vs-merge backend/workflow source equality |
| PR artifact13516329433 | ZIP SHA2569f39370f525ce8be50b3575444021fb012d63eed3cb001377e792dead53257a2 verified after download; source tree751ae2fa309076a59dbd3e0fd9522b68b360a6f9 |
| [Missing-command development RED42243905417](https://github.com/alireza-anari/cac-project/actions/runs/42243905417) | Real PG/dblink positive first; original command assertion `None !=1: Real quorum authority command not implemented`; no setup error. Same assertion GREEN after actual CAS implementation; this is NOT required H-05 security-mutation evidence. |
| Local real TLS redirect negative | Original `Denied not raised: Redirect escaped the pinned HTTPS authority endpoint` assertion reproduced; same probe GREEN after redirects disabled, sink not contacted. Synthetic marker only, independent local TLS/HTTP processes; NOT etcd/PG proof. CI also executes the fixed probe. |

Pinned experimental dependency: upstream etcd/etcdctl/etcdutl3.6.16, source0b065e61c679ea81f6862bb24c9815f7fc673966, archive SHA256c8c0d96d8292ef085deabbf735e9561d3d396768e4d606df005aa25964f21911 **actually checked in CI before extraction**, no vendor/technology approval. PostgreSQL17.11, official image digest839fbb5a4942a7758dd93e18b42ea5649807491a0545b5eeeb8f0b8bb11857a5. Python3.12.15/hash-locked inherited dependencies. H PgBouncer integration is NOT_RUN.

The seven cases cover: actual five voter membership and PG TLS dblink; atomic epoch reservation/state/journal MVCC revision; three-current-survivor progress; majority availability loss denies current reads (its command probe was confounded by RESERVED phase); sequential two-member fresh learner catch-up/explicit promotion; two-contender CAS one winner; redirect confinement. No test yet protects application data via an H overlay.

Actual Push witness: cluster14314942586496979653; preserved r1=14944756383011589575, r2=2789022262654016710, r3=12407635188785387957; original majority data never restored. Learner r4=9629421636026476538 at term3/index39, explicit promotion index41. Learner r5=7807977365134970679 at term3/index44, explicit promotion index46. Both transitions were four voters+one learner, then five voters, not five voters throughout. Namespace state/journal revision10/headfcc003782230c4fab99dde002f67a9beb00a3737264cc598e1f93d7ba83e0a94 survived. The atomic independent namespace case recorded state/journal revision4/headabcf536a8be625760e7bfac30d02c1cc30bbf8f42a2fafaa95d2292c1a3eb9b3. These are distinct application-journal and Raft indices, never interchangeable.

At9268aa4, learner observation checks actual learner ID/status, a matching state head and two journal rows with matching last MVCC revision. A follow-up strengthens this with response member/cluster identities and full key/value/revision equality against a current survivor at the same pinned revision. Independent review also found that the outage command would already be denied in RESERVED phase; the follow-up uses an eligible EMPTY target, paired healthy control and exact request retry to resolve possible lost ACK without assuming abort. Do not claim this added check ran at9268aa4. No byte-identity observation of internal Raft WAL was performed.

The strengthened source checkpoint0bdbbc93859f5e0c371e15e4a080a4a148e91e47 also passed [Push42246319003](https://github.com/alireza-anari/cac-project/actions/runs/42246319003) and [PR42246333139](https://github.com/alireza-anari/cac-project/actions/runs/42246333139), seven cases without skips. This run includes full learner journal key/value/revision comparison, response cluster/member identity assertions, and a paired healthy eligible EMPTY reservation control followed by actual outage and exact request retry; the earlier command-confounding and incomplete-prefix evidence limits are now corrected for this narrow preflight. Full OPEN recovery and mandatory data-path enforcement remain unproved. Next commit adds separate lifecycle cases test-first; a development missing-ACTIVE RED is expected until implemented, not security acceptance.

## Setup failures, not security RED

The first runs failed at authenticated gateway bootstrap: external client certificate CN=root is explicitly rejected by pinned upstream `server/embed/serve.go` after auth enable. A dedicated CA-signed empty-CN client certificate fixes the compatibility problem; mTLS, server SAN verification, root password/token and peer certificate checks remain enabled. `Accept` alone did not resolve it. Independent reviewer confirmed the pinned-source cause. Full private member logs/keys/configs are excluded from artifacts.

The first learner attempt failed with actual503/code14 `etcdserver: unhealthy cluster` following availability recovery. Controller now retries only that strict refusal, re-observes membership, never disables server strict health, and stops on unexpected identities. New learners reject Authenticate/linearizable reads; the observer obtains a fresh token through a current voter, then checks local serializable data before promotion. Old voter directories are quarantined and never restarted as restored voters. Literal old-snapshot import into an existing live learner is unsupported/NOT_RUN; ordinary new-identity protocol replacement must not be relabeled snapshot import.

## Incomplete security matrix

| Required slice | Status at this checkpoint |
|---|---|
| Real durable five-voter root + atomic epoch reservation | OBSERVED_PASS, bounded cases above; signer/OPEN atomic state transitions incomplete |
| Actual sequential minority replacement as learners | OBSERVED_PASS for root reservation history only; full OPEN recovery NOT_RUN |
| Complete hash-linked journal in authority reads | DESIGN_SPECIFIED / implemented for genesis+reserve; corrupt/incomplete replay adversarial cases NOT_RUN |
| Mandatory independent SQL/issuer/RLS read **and write** / legacy / pool admission | NOT_RUN; no H guard installed; do not run protected-data scope or claim H authorization enforcement yet |
| Actual old W restore against current R | NOT_RUN |
| Durable OPEN, FIRST_USE_GRANTED/revoke/known close/UNKNOWN | NOT_RUN; missing at this checkpoint |
| Actual PG/PgBouncer transaction reuse/cancel/rollback with R | NOT_RUN |
| Crash/lost ACK/stale signer/policy / delayed permit | NOT_RUN |
| H-05 five-control restored-original-assertion sensitivity | NOT_RUN; development REDs above are not substitutes |
| 169 inherited cases | Original source byte-identical outside new h_quorum; separate applicable CI rerunning; final-head verdict pending |
| Historical D C-only rollback | Remains FAIL_SECURITY, original source/assertion unchanged; no new-root claim |
| Final independent source/evidence review | Pending; separate read-only stage1 source/evidence review completed and its limitations recorded below |

## Independent stage1 review

A separate read-only reviewer inspected committed source9268aa4 and the downloaded actual PR artifact. No edits or tests were delegated to that reviewer. Findings: (1) outage command denial had an already-invalid RESERVED precondition; (2) learner journal equality needed full key/value proof; (3) actual PG transport validation covered only status, while redirect negative covered only the etcd HTTP client, with wire authentication/parser/CA negatives NOT_RUN; (4) no application authorization, signed guard/verify, OPEN or pool acceptance follows. The first two are addressed by stronger pending tests, requiring new execution evidence. Items3/4 remain explicit stage2/3 gates. There was no demonstrated unsafe application permit because H has no application-permit path yet. This review is a stage1 checkpoint review, not the required final whole-experiment verdict.

## Boundaries and remaining risks

P0: no all-route H admission or lifecycle proof yet; complete H acceptance BLOCKED. R majority rollback/all-root loss, old-root+old-verifier rollback, physical clone, custody and actual independent administrative failure domains are excluded/NOT_RUN; no automatic detection claim. Lane3/OPEN_UNKNOWN clearing BLOCKED, with no timer/manual hard-fence release.

P1: all five processes, controller, certificates and PG containers share a disposable CI host; this is process separation and actual consensus, not operational independence. Controller and root service own the experimental credential/configuration boundary. Etcd simple-token fixture is an experimental testing mechanism, not an approved production key system. Full-state-per-entry application journal has unmeasured growth, latency, capacity and retention cost; no benchmark or HA/DR claim. Gateway is a narrow test PG-wire façade, not a public SQL service. The fixed redirect regression and redact-before-truncate hardening came from independent preflight review.

SOURCE-001/GATE-SOURCE BLOCKED; Gate9 and issues23/28 OPEN; protocol PROPOSED. No Production, real identity/onboarding, APR amendment, merge, baseline or Sprint0 acceptance. Next execution resumes from these commits, not from the parent or R0 design.
