# S0-03 — برنامه ادغام مشروط SEC-REV-001

وضعیت: **DESIGN / NOT_EXECUTED / NOT_MERGED / SOURCE_UNVERIFIED**. این سند برنامه کار است؛ هیچ فایل backend یا migration فرضی تولید نشده است. مبنا v3.37 / APR-036؛ candidate همان بایت S0-02 است.

## پیش‌نیاز و ترتیب

1. Management/مالک منابع باید ZIP واقعی Freeze v3.37، scaffold v3.38 و سورس v3.39 شامل migrationهای اصلی را در همین workspace ارائه کند؛ یا URL دقیق repository مجاز، ref/commit قابل‌خواندن و نگاشت نسخه‌ها. SOURCE-001 قبل از احراز این منابع بسته نمی‌شود.
2. Work hash/provenance و diff v3.38→v3.39 و Freeze→backend را ثبت کند؛ مسیر مدل‌ها، سرویس‌ها، auth، routes و graph migration را از همان سورس استخراج کند. هیچ مسیر مقصد یا شماره migration در این سند مفروض نیست.
3. نسخه Python/Django/DRF/PostgreSQL/driver، lockfile، تنظیمات isolation/pool و نقش‌های DB را از baseline ثبت و محیط disposable با داده مصنوعی فراهم کند. نبود هرکدام BLOCKED، نه مجوز ساخت baseline جایگزین.
4. ابتدا regression نقص روی adapter واقعی و baseline اجرا و RED ثبت شود؛ سپس کوچک‌ترین انتقال bugfix با بررسی schema/API/authorization صورت گیرد. patch مستقل نباید کورکورانه روی ORM اعمال شود.
5. unittestهای مرجع، contract tests، HTTP session/MFA/CSRF، PostgreSQL role/isolation و طرح رقابت این بسته اجرا شوند. فقط پس از review و تصمیم Management integration پذیرفته شود؛ اجازه push/deployment از این برنامه حاصل نمی‌شود.

## نگاشت فایل‌ها و تعارض‌های قابل انتظار

مسیرهای مبدأ زیر نسبت به `candidate/cac-v3.40-onboarding-module` داخل آرشیو S0-02 هستند. مقصد تا بازیابی سورس **احراز نشده** است.

| مبدأ واقعی | محل مقصدی که باید کشف شود | انتقال یا بررسی | تعارض/وابستگی |
|---|---|---|---|
| `cac_onboarding/service.py::revoke_capability` | service/command مربوط به revoke در backend | ابطال pendingها مستقل از تعداد grant؛ audit در همان transaction | نام فیلدها، revoked/accepted status، transaction nesting، error mapping |
| `service.py::accept_invitation` | مسیر واقعی accept | بازخوانی state و authorization زیر هماهنگی قفل با revoke | snapshot قدیمی، scope قفل، upsert/reactivation و ترتیب commit |
| `service.py::issue_invitation` | مسیر واقعی issue/delivery | دعوت تازه پس از revoke با مجوز جدید همچنان مجاز؛ ارسال امن | outbox، hash token، idempotency و ترتیب رقابت issue/revoke |
| `cac_onboarding/policy.py` | capability/ownership و MFA policy مصوب | حفظ owner immutable، held-capability و sensitive MFA | مدل identity واقعی، تازگی MFA و تغییر permission بین check و write |
| `cac_onboarding/storage.py` | models، constraints، migrations و repository واقعی | فقط مقایسه؛ SQLite schema جایگزین PostgreSQL نیست | unique دائمی SQLite در برابر unique-active طرح، FK مرکب، RLS، audit append-only |
| `integration/ADAPTER_PORTS.py` | IdentityResolver واقعی | adapter fail-closed و اعتبار server-side | fake resolver نباید wiring محصول شود |
| `tests/test_revocation.py` | suite service/DB/HTTP واقعی | ۱۳ oracle به fixtureهای واقعی منتقل شوند | تفاوت dialect/transaction و Django TestCase در برابر TransactionTestCase |
| `tests/test_onboarding.py` | suite regression | ۳۲ آزمون مرجع حفظ؛ موارد معادل integration افزوده | SQLite concurrency معادل PostgreSQL نیست |
| `integration/openapi-onboarding-addendum.yaml` و G3 | OpenAPI و routes frozen واقعی | diff و conformance مستقل؛ bugfix route جدید ندارد | cancel/revoke در YAML فعلی غایب؛ API-001/API-002 همچنان باز |

## مرز تغییر و CR

انتقال شرط اجرای ابطال pending و audit مؤثر، با semantics مأموریت S0-02، bugfix است. در candidate هیچ API/DB/policy تغییر نکرده است. Django adaptation احتمالاً SQL پارامتری را با ORM و transaction.atomic/قفل مناسب جایگزین می‌کند؛ این تنها **موضوع بررسی آینده** است، نه کد ساخته‌شده یا راهکار مصوب.

قفل روی ردیفی که همیشه وجود دارد (برای نمونه Store موجود یا anchor معتبر در baseline) می‌تواند accept/revoke را حتی بدون grant هماهنگ کند. انتخاب نهایی نیازمند شناخت lock order و scope واقعی است. قفل صرفاً روی grant غایب کافی نیست. ایجاد جدول anchor، advisory-lock contract، تغییر isolation، تغییر نقش/RLS، schema audit یا امضای API اگر لازم شد، پیش از اجرا CR جدا با schema/API diff، تهدید، backward compatibility، rollback و آزمون ارائه شود. این سند چنین تغییری را تصویب نمی‌کند و فعلاً ضرورتی احراز نشده که CR اجرایی جدید بسازد.

مصوبات APR-033/034/035 و Freeze APR-036 دست‌نخورده‌اند. bootstrap، migration graph، forward/reverse، composite FK، ENABLE/FORCE RLS و runtime/provisioner غیرمالک باید در سورس واقعی بررسی شوند؛ عدم تغییر SQLite schema شاهد سلامت آن‌ها نیست.

## معیار خروج

- source hash/commit و mapping مقصدهای واقعی؛ diff کوچک و traceable، بدون overwrite migration تاریخی.
- PostgreSQL و driver pinned؛ metadata نقش واقعی، nonowner/NOBYPASSRLS و context transaction-local با fail-closed و pool-reset tests.
- پذیرش آزمون‌های `PG-RACE-01..08`، regression و security integration؛ audit و تغییر DB اتمیک، zero cross-store effects.
- یافته‌های unresolved با owner؛ review Architecture برای هر CR لازم و Management برای پذیرش. تا آن زمان GATE-INTEGRATION و GATE-PG-RACE مسدودند.
