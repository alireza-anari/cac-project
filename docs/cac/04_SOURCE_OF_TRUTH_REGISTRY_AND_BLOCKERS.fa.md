# فهرست واقعی سورس‌های در دسترس و موانع تحویل

**در زمان ساخت بسته اسناد 2026-10-26:**

| منبع | وضعیت واقعی | hash (SHA-256) |
|---|---|---|
| `v3.37 Architecture Freeze` | مصوب `APR-036` اما اصل ZIP فعلاً موجود نیست؛ `SOURCE-001` باز | ثبت‌نشده در این بسته؛ **حدس نزنید** |
| `v3.38 Django Scaffold` | در گفتگو ساخته و گزارش شده؛ بایت‌ها در این محیط موجود نبودند | ناموجود |
| `v3.39 PostgreSQL RLS` | در گفتگو ساخته و گزارش شده؛ بایت‌ها در این محیط موجود نبودند | ناموجود |
| `v3.40 Standalone Onboarding` | ZIP قابل‌بازیابی و سالم؛ ۳۲ آزمون مستقل Python/SQLite را در این نوبت دوباره اجرا کردیم | `e685e8872e953aff66daeeb6c551332f0dc6a178269f4041382c2f84c8e1118e` |
| `v3.41 Work Handoff` | ZIP سالم و manifest داخلی verified؛ سند انتقال کار، نه سورس Freeze | `08316862c0afa60d500f7619dccaaee02ea92f60148111531e0f0aa6cee938bf` |
| `v3.42 Project Sources` | همین مجموعه خلاصه منابع برای سه چت؛ هیچ Freeze جدید | در `MANIFEST.sha256` همین بسته |

## مانع‌های اولویت‌دار
- `SOURCE-001`: بازیابی سورس و آرشیو Freeze واقعی، diff و ادغام بدون بازسازی حدسی.
- `DB-001`: Django/PostgreSQL migration graph، FK مرکب، RLS semantics و role test در DB واقعی.
- `IDENTITY-001`: IdP، MFA freshness، verified owner، secure invitation delivery، CSRF.
- `PROVISION-001`: role provisioner با least-privilege، idempotency و onboarding integration.
- `PROVIDER-001`: vendor/model/region/DPA/terms/retention، هزینه و منطقه داده؛ egress خاموش تا حل.
- `API-001`: OAS 3.1.1 base و افزوده onboarding با linter مستقل و client/server conformance.
- `UX-001`: پنل ۴بخشی، تست دسترس‌پذیری، onboarding ساده.
- `WOO-001`: نسخه سازگار Woo/WordPress/PHP، reliability push/Cron و هماهنگی تستی.
- `OPS-001`: keys, monitoring, backup, disaster recovery, audit retention.
- `BILLING-001`: پرداخت/مالیات و قیمت نهایی اشتراک.

## قاعده Work
اگر repo/Freeze موجود نیست، **کار متوقف مطلق نمی‌شود**؛ با برچسب `NOT_MERGED / SOURCE_UNVERIFIED` فقط کار مستقل قابل‌اثبات انجام بده. integration یا baseline frozen را با حدس اعلام نکن؛ هر conflict با diff و CR به معماری/مدیریت برگردد.
