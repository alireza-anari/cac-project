# S0-09F independent read-only security review

**W_ORACLE_ASSUMED / LANE1_ONLY / ROOT_AND_ORPHAN_RECOVERY_UNPROVED**

This is an independent automated-agent review, not human certification, formal verification, protocol acceptance or production authorization. The reviewer received the fixed Lane1 design/Issue26 restrictions, inspected files read-only and did not implement changes. The primary implementer verified reported defects and owns the experiments. No previous PR was merged. SOURCE-001/GATE-SOURCE BLOCKED; Gate9 and Issue23 OPEN.

## Reviewed checkpoints

- Stage1 five reviewed blobs independently matched `aaf89ba18f0bf49e1c4ba6a80b3c702ad963ce7e`. Ten API GREEN tests did not cover the discovered CLOSE/UNKNOWN race or attest/verify surface.
- Stage1 correction `0f842161effd1c033cb3634b3398a92130f074f1`: real race RED at `5fe69f5`, unchanged assertion GREEN after row locking;14 actual API methods PASS Push42193880340/PR42193886361.
- Stage2 source review covered catalog, lab/admission, broker, guard and inverse overlay. Corrected implementation `7f6652574ddb726f49a5236d5f986a64c8e5984c` has25 observed new GREEN methods Push42196141325/PR42196150321. Runtime evidence was read by the implementer; independent reviewer source conclusions are not substituted for execution.
- Stage3 working source was reviewed for wire ACK loss, crash worker, fault cases, lifecycle hooks and mutation restoration. No new blocking enforcement defect found in that inspection. Reviewer required two additional crash cuts (C-finish before W-close; uncommitted W-close), both added and observed PASS across W restart in Stage3. Final independent source/log/artifact review completed at `168543a32a937c56113c1b51b26b2fb82af17257`; details below.

## Findings and resolution

| ID | Priority | Finding | Resolution / evidence |
|---|---|---|---|
| F-R-01 | P0 within candidate lifecycle | CLOSE read OPEN without a row lock; a concurrent UNKNOWN could commit then be overwritten CLOSED | Real two-session row-lock barrier reproduced assertion FAIL in both Push42193663094/PR42193670186. SELECT FOR UPDATE before checking; same assertion GREEN in Stage1 correction. No UNKNOWN clearing API added |
| F-R-02 | P0 at old-verifier restore boundary | NOLOGIN and backend termination in one transaction left a concurrent-login window; signal-only termination did not prove drain | Commit NOLOGIN first, terminate with wait, fresh zero-session scan before DDL. Stage2 admission tests GREEN; actual active PgBouncer backend drain/zero-session observation PASS in Stage3 |
| F-R-03 | P0 outcome-binding contract | ABORT branch accepted rollback of a replacement transaction as original operation outcome | INTRANS verifies original SID/PID/fullxid before rollback; INERROR remains UNKNOWN. Actual COMMIT/BEGIN + exception regression GREEN; no guessed ABORT; cancellation availability intentionally blocked |
| F-R-04 | P1 interface/test gap | Attestation had empty-digest wildcard; old OPEN lacked explicit current policy/namespace/manifest comparison | Strict stored digest/control binding; positive proof + wrong nonce/proof/hold/binding/revocation/control-version negatives added and GREEN |
| F-R-05 | P1 restore identity obligation | SID/fullxid alone does not identify a restored app incarnation | Trusted supported restore rotates admitted actor incarnation; runtime response checks it. Physical same-identity clone resistance remains BLOCKED/NOT_RUN |
| F-R-06 | P1 evidence scan scope | Current signing-key scan did not cover keys replaced by independent test genesis | Store historical generated keys only in private fixture config and scan against all of them; no key material uploaded |
| F-R-07 | P1 crash coverage | Initial schedule bracketed but did not execute C-closed/W-open and uncommitted W-close states | Add both actual os._exit cuts and W restart assertions; PASS in the 40-method Stage3 suite |
| F-R-08 | P1 evidence fidelity | Stage3 delayed revoke used unadmitted B; several contender negatives could deny before OPEN exclusion | Actual expected-state failure at `9e07ea6`; restore/admit B and positive W status before contenders at `25e555f`. Stronger 40-method Stage3 rerun PASS; earlier reason-specific claim relies on corrected admitted-B evidence |
| F-R-09 | P1 fault-causality evidence | NULL issuer args/missing tickets could deny independently of injected identity/channel fault | New helper proves exact live issuer args/ticket and committed-context RLS first, then requires both SQLSTATE42501 after mutation. Early setup flag prevents vacuous pass. Initial helper exposed uncommitted ledger, fixed by legitimate committed issuance; PASS in the 40-method Stage3 suite |
| F-R-10 | P2 diagnostic capture | PREPARE55000 was replaced by conservative cleanup FenceDenied before outer assertion inspected it | Capture55000 at the statement, independently expect FenceDenied/UNKNOWN, do not relax cleanup |

No inherited assertion/control was weakened. Wrapper installation initially failed because the NOLOGIN guard lacks CREATE on public app schema; correction creates wrappers as the migrator and sets explicit guard ownership. CREATE privilege was not granted to runtime, issuer or guard to hide the failure.

## Security boundary assessment

The bounded mechanism can test online deny-only integration under assumed W. It does not prove W itself is nonrollbackable, its return channel is a production authenticated root, or any identity is noncloneable. External admission/controller and trusted coordinator are part of the model, not adversaries defeated by this proof. Superuser/host compromise is excluded. No orphan timeout, reconciliation or manual clearing is present. A safe negative result is a permanent availability block.

The legacy C-only rollback remains a real P0 FAIL_SECURITY. A separate current-W candidate GREEN does not repair or rename it. Any claim beyond the actual executed matrix is prohibited. Final independent read-only recommendation: accept only the executed conditional Lane1 integration observations at `168543a`, with no remaining blocking defect identified within the reviewed bounded model. Exact final report-commit CI will be separately receipted in Issue26/PR27; the review does not pre-approve an untested future executable delta. Retain Lane2/Lane3 BLOCKED, PROTOCOL_PROPOSED and no production permission.

## Final independently checked evidence

The reviewer independently fetched/decoded PR42199159766 job127829873785 and Push42199153251 job127829851954. Both show 40 distinct new tests GREEN before and after mutation restoration; three intended one-assertion REDs with zero errors/skips, exact catalogs restored and same probes GREEN. The W_SQL mutant actually allowed C1/A new issuance and scoped RLS under current W2 before the unchanged denial assertion failed.

Reviewer also checked nine unresolved crash/restart cuts, actual lost W OPEN and local issuer COMMIT replies, valid-live-path fault controls, admitted contender exclusion, pool reuse and active-session quarantine. These are bounded observed schedules, not proof of every failure/interleaving.

Downloaded PR artifact13492713468 verified ZIP SHA256 `720af6c2370eb503dfb4e1c2cf0d523d7808668df468a89b6d086c7bb342bc65`. Tested synthetic merge `8c9a1c79b04b0e4a9125cbb98fc5bcf1332c11f3` and head `168543a32a937c56113c1b51b26b2fb82af17257` share F source tree `367218ab9f1b287f3fb7f4ce615bc068415018bc`, matching local reviewed source. Inherited backend diff versus parent is empty; inherited workflow changes only broaden routing. The implementer separately verified Push artifact13493089210 SHA256 `b079dc2e807813032c5eafd18552e7f77b0c3c4410ca336004008af86b61214f`.

P0 legacy C rollback, actual W-root irreversibility/custody/authentication, physical clone resistance and orphan reconciliation remain unresolved/BLOCKED. P1 trusted controller/coordinator, same-host failure domain, bounded catalog/schedule coverage and potentially indefinite fail-closed downtime remain explicit. Accepted review language: **INTEGRATION_PROVEN_ONLY_UNDER_ASSUMED_W / S0-09F_BOUNDED_ORACLE_INTEGRATION_EVIDENCE_ONLY / W_ROOT_AND_ORPHAN_RECOVERY_UNPROVED / PROTOCOL_PROPOSED**. No Lane2/Lane3, production or protocol approval.

Implementer subsequently verified Stage3 full94 Push42199153484 and PR42199159830 completed SUCCESS; all eight applicable workflows on168543a are complete. Final documentation-head CI remains pending at document creation and will be separately receipted after completion; no executable changes accompany that report.
