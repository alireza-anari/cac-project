# PV0-01 — Local preview handoff

Date: 2026-11-07. Authorization: CAC issues #42/#43 and `docs/management/CAC_PREVIEW_V0_PREVIEW_FIRST_DECISION_R0.md` on parent main `f9f465c3387833d44e537c163c9dacff75e352ac`.

Status: **LOCAL_PREVIEW_HTTP_VERIFIED / DEMO_RULE_BASED / MANUAL_BROWSER_BLOCKED / PRODUCT_OWNER_FEEDBACK_PENDING / PRODUCTION_BLOCKED**.

Full source is in this directory. Start with [README.fa.md](README.fa.md). Exact final commit, Draft PR, downloadable archive, SHA-256 and final-archive verification receipt are published in execution [Issue #43](https://github.com/alireza-anari/cac-project/issues/43). The archive includes a per-file `MANIFEST.sha256`; a document cannot embed its own containing archive hash without changing it.

## Measured verification

Commands below used Python 3.12.14 in a dedicated virtualenv. Exact dependency/runtime versions are in `evidence/versions.json`; official Django release verification links are in the README. No CI/workflow was added or dispatched. Evidence text has trailing whitespace normalized; the one synthetic HTML response containing an ephemeral CSRF value is explicitly omitted.

| Command / evidence | Exit | Observed result |
|---|---:|---|
| `python manage.py check` → `evidence/check.txt` | 0 | No system-check issues |
| `python manage.py makemigrations merchant` → `evidence/migrations.txt` | 0 | New isolated Preview migration generated |
| `python manage.py migrate` → `evidence/migrate.txt` | 0 | Native auth/session + Preview tables applied to local SQLite |
| `python manage.py makemigrations --check --dry-run` → `evidence/migration-drift.txt` | 0 | No model/migration drift |
| `python manage.py test --verbosity 2` → `evidence/tests.txt` | 0 | **17 distinct tests**, no failures |
| `python -m pip check` | 0 | No broken dependency requirements |
| Initial behavior-first run → `evidence/red.txt` | 1, expected | 6 failures because app routes were not implemented yet; 1 boundary check passed |
| First implementation → `evidence/tests-first.txt` | 1 | 3 subtest failures: method rejection preceded owner lookup on read-only routes; fixed to check ownership first; assertions retained |
| Two regressions → `evidence/regression-red.txt` | 1, expected | Saved assistant editor values were overridden by initial defaults; arbitrary search cap hid stored items. Fixed; both covered by final suite. Synthetic HTML response omitted because it contained ephemeral test CSRF values |
| Reviewer-discovered nested-name regression → `evidence/review-red.txt` | 1, expected | Shorter name obscured exact longer product name; fixed, final suite covers it |
| Checkpoint ZIP: `python tools/verify_zip.py ZIP NEW_DIRECTORY` → `evidence/cold-checkpoint.txt` | 0 | Fresh venv/dependency install, new DB/key/account, check/migrate and then-current 14-test suite; actual local HTTP journey; stop/start persistence |
| **Final ZIP**: same verification command, fresh different directory | See #43 final receipt | Repeated after source/review fixes and packaging; final log is delivered alongside the archive rather than recursively inserted into it |

The 17 methods cover login/unauthenticated denial, Store/product CRUD, foreign owner GET/POST rejection, same-owner cross-Store product rejection, one-assistant DB constraint, invalid inputs/prices/tone/question bounds, HTML escaping, actual CSRF rejection and valid-token mutation, stored-data/current-price and unknown replies, assistant edit persistence, full-catalog/nested-name matching, no public routes, remote host/address rejection, forbidden bind, and runtime socket/DNS rejection. Socket rejection tests are intercepted before network transmission; they do not contact an external target.

The HTTP verifier starts and terminates real Django subprocesses in one sandbox, posts through native login and actual CSRF middleware, creates a Store/two products, changes assistant settings, sends questions, changes price, checks fallback, then restarts the server and verifies SQLite/session/assistant/current answer persist. This is **HTTP automation, not a browser walkthrough**.

## Manual/visual evidence — NOT_RUN

The cloud browser's `127.0.0.1:8000` is not the application process namespace; it returned an unrelated bearer-token service, not CAC. No credentials were entered there. A local-server launch outside the execution sandbox was rejected automatically because the environment disables sandbox approval/escalation. No exposure, port forward, proxy deployment or other bypass was attempted.

Consequently the full manual browser journey, responsive/mobile rendering, keyboard/focus interaction and screenshots are **NOT_RUN / environment-blocked**. No generated image is presented as an application screenshot. Windows and macOS setup are documented but **NOT_RUN**; Linux/Python local HTTP cold installation was actually executed. This is a known acceptance gap, not proof of visual usability. Owner hands-on feedback remains pending; use the README's eight steps on the owner's own local machine.

## Lightweight independent read-only source review

A fresh reviewer agent inspected models/migration, forms, views, rules, templates/CSS, settings/setup/network/bind guards, tests, packaging and existing evidence. Verdict: **LOCAL_SOURCE_READY_WITH_BROWSER_LIMITATION**; no critical/important source finding within the synthetic localhost scope.

Two minor findings were fixed and read-only rechecked: mobile CSS hid the only logout control (logout moved to always-visible topbar, POST+CSRF retained); nested product names could produce an unresolvable exact-name prompt (longest nested full-name matching added with RED→GREEN regression). Separate-agent role independence is not external certification or merge/owner acceptance. The reviewer did not execute tests or inspect local credentials.

## Open limitations and stop/feedback point

- Rules are deliberately simple; no language model, embeddings, semantic reasoning, purchases, AI-provider/Woo calls or external runtime requests. Duplicate identical product names may remain ambiguous; use distinct names. Lists show 20 names; name lookup uses stored catalog, not just that list.
- No public Live/widget/API, registration, MFA/IdP, billing, domain/contact proof, production tenant/RLS or automatic 30-day transcript deletion. Local demo messages remain until local state is removed. No real business/customer data.
- Local HTTP development server, no TLS or public login throttling. POSIX private-file modes do not establish Windows ACL security; Windows was not executed. Python audit guards are not an OS sandbox against malicious native code. SQLite write concurrency and product-scale load were not certified.
- A repeated POST may create another demo message; no distributed/idempotent authority claims. One private assistant uses a database OneToOne constraint; no actual public-Live concurrency proof.
- Full Production, canonical source/baseline and Source gates remain blocked. Gate #9 and #23/#28/#33 OPEN; SOURCE-001/GATE-SOURCE BLOCKED; D historical rollback FAIL_SECURITY; G1–G5 DESIGN_BLOCKED; Lane3 BLOCKED; root policy retirement and literal stale Raft snapshot/WAL NOT_RUN. H evidence remains within its prior non-restored-majority experiment only.

**Stop feature expansion here.** Deliver this executable slice and its honest browser limitation for owner experience; obtain accept/revise/reject and top three usability priorities before PV0-02. This is not a claim that every acceptance item or Production gate has passed.
