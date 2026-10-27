# قراردادهای پایه امنیت، داده و گیت Live

## Tenant / Store / Capability
- مرز اطلاعات: همه اطلاعات فروشگاه با `tenant_id/store_id` معتبر در API، service و DB ایزوله شوند؛ PostgreSQL FK مرکب واقعی + `ENABLE/FORCE RLS`, policy `USING/WITH CHECK` و app-runtime فاقد مالکیت، superuser و `BYPASSRLS`.
- membership جایگزین capability نیست؛ قابلیت مجزا برای دیدن متن گفتگو، مدیریت دامنه، فعال‌سازی دستیار، انتشار دانش، contact management و تغییر مجوزها. worker و provisioner roleهای مجزا با least privilege باشند.
- request identity transaction-local و بر اساس احراز هویت server-side؛ نباید از user-submitted tenant/store context برای تنظیم RLS استفاده شود. در نبود context دسترسی DB رد شود. GUC به‌تنهایی در برابر SQL injection boundary کافی نیست.
- یک Store → چند Assistant؛ unique conditional روی حالت public Live (V1 فقط یکی). gate تماس، domain proof، installation, reviewed knowledge, owner approval و vendor مجاز را قبل از Live و در هر public request enforce کنید.

## API و secrets
- admin same-origin session + CSRF + MFA برای اعمال حساس؛ public visit bearer جدا از admin؛ connector HMAC+timestamp+nonce+epoch و replay protection؛ pairing proof یک‌بارمصرف.
- `If-Match` و idempotency برای mutation؛ durable outbox، safe retry؛ از plaintext credential، خام transcript و داده Woo private در log/queue/export خودداری شود.
- URL ingestion با allowlist، DNS/redirect checks، محدودیت SSRF؛ فایل quarantine/scan و human review قبل release؛ vector RAG با فیلتر pre-query Store+release.
- public widget origin, CORS و widget ID اثبات هویت خصوصی نیستند؛ تنها داده public-safe و abuse/budget guardrails مجاز.

## Release/Acceptance Gates
| Gate | حداقل شاهد قابل قبول |
|---|---|
| `SOURCE` | فایل اصلی Freeze/repo commit واقعی، SHA، تطبیق و conflict log. |
| `BOOT/MIG` | نصب reproducible، Django check، migration up/down روی PostgreSQL آزمایشی، diff. |
| `TENANT` | حداقل دو Tenant/دو Store و یک Tenant با دو Store؛ تست cross-store denial با نقش app غیرمالک. |
| `ONBOARD` | owner identity verified، create idempotent، invite/revoke، MFA واقعی، عدم escalation و audit. |
| `ASSISTANT` | readiness، race activation، تماس آخر، Pause فوری و جلوگیری از دو Live. |
| `WOO` | امضا، nonce/replay، dedupe/reconciliation، پرهیز از order/customer، قیمت/موجودی معتبر. |
| `KNOWLEDGE/AI` | source review و دو reviewer برای حساس، provider approved، RAG scoped. |
| `WIDGET/RETENTION` | iframe security، visit isolation، انقضای ۳۰روزه و purge/backup behavior. |
| `PRODUCTION` | همه integration/E2E/security/legal/performance/monitoring/owner approvals لازم. |

**هیچ PASS بدون دستور/محیط/لاگ واقعی ثبت نشود**. وجود کد migration یا schema به معنای اجرای آن نیست.
