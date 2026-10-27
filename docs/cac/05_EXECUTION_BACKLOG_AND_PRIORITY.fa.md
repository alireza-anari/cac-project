# برنامه اجرای Work با اولویت امنیت

| Sprint | هدف | تحویل قابل قبول و گیت |
|---|---|---|
| `S0 — Source & Bootstrap` | شناسایی repo/Freeze/ZIP، diff نسخه‌ها، نصب reproducible محیط، CI، صحت OpenAPI و migrations | commit/hash، clean setup، conflicts، تست ساختاری، گزارش `SOURCE-001` |
| `S1 — Tenant & Onboarding` | Django/PostgreSQL RLS/FK/roles، امن‌سازی provisioning، دعوت و grant، MFA/CSRF | negative isolation tests روی DB واقعی و app role، owner creation، idempotency و audit |
| `S2 — Assistant + Merchant UX` | چرخه Preview/Ready/Live/Pause و Contacts/Domain، اسکلت پنل ۴بخشی | concurrency safety، last-contact pause، UX onboarding بدون Live جعلی |
| `S3 — Woo Connector` | افزونه رسمی WP/Woo، pairing/HMAC/epoch/dedup، catalog snapshot/events/reconciliation | تست نسخه‌های مشخص و ارسال فقط product public؛ price/stock freshness معتبر |
| `S4 — Knowledge + AI` | FAQ/Policy review، URL/file safe ingress، pgvector scoped retrieval، provider adapter | دو reviewer برای حساس، no cross-store retrieval، no unapproved provider egress |
| `S5 — Widget + Conversations` | iframe widget کلیکی، visit tokens، polling، chats، retention | browser tests، abuse tests، no cross-visit transcript، retention ۳۰روز |
| `S6 — Billing + Ops + Release` | ساده‌سازی اشتراک ماهانه، internal usage ledger، observability، backup/incident | release candidate و production gate مستقل؛ بدون ادعای SLA حدسی |

## سیاست موازی‌سازی
Management می‌تواند طراحی UX را هم‌زمان با S1 روی mock پیش ببرد، اما انتشار endpoint با داده واقعی به عبور از گیت TENANT/RLS وابسته است. Work مسئول اجرای واقعی کد، اسکرین‌شات یا دموی مستند، migration و logs است. معماری مسئول تغییر قرارداد. Management مالک اولویت و signoff است.

## قالب گزارش پایان هر Sprint
`source_ref` (commit/ZIP+SHA)؛ `changed_files`؛ `schema_diff`/`api_diff`؛ شناسه‌های `CR/ADR`؛ محیط و command واقعی؛ جدول تست‌های `PASS/FAIL/SKIPPED/BLOCKED`؛ blockerها؛ ریسک امنیتی و residual؛ سه اقدام بعدی با مسئول مشخص.
