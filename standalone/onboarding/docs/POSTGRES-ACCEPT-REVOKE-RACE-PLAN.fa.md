# PostgreSQL accept/revoke — طرح آزمون واقعی پس از بازیابی baseline

**DESIGNED / NOT_RUN / BLOCKED by SOURCE-001 and DB-001.** این فایل طرح harness است، نه migration یا تستی که اجرا شده باشد. هیچ نتیجه PostgreSQL از SQLite استنتاج نمی‌شود.

## محیط و fixture

- PostgreSQL disposable با نسخه و isolation دقیق backend بازیابی‌شده؛ driver و Django/DRF pinned. از دیتابیس مشتری، credential واقعی یا provider خارجی استفاده نشود.
- Tenant A/B؛ Store A1/A2 زیر A و B1 زیر B؛ owner A/B، manager کم‌اختیار، target T و target U. برای سناریوی اصلی، T یک دعوت معتبر برای `store.view` در A1 دارد و **هیچ grant فعالی ندارد**. variant دوم grant فعال همراه دعوت معلق است؛ variant سوم دعوت چندcapability است.
- actor و target از identity fixture معتبر server-side می‌آیند؛ fake آزمون فقط در harness مجاز است. هر connection context خودش را transaction-local تنظیم می‌کند؛ context از payload مشتری اعتماد نمی‌گیرد.
- دو worker مستقل با دو connection واقعی و `pg_backend_pid()` متفاوت: A برای accept و R برای revoke. در هر thread اتصال تازه یا `close_old_connections` مناسب؛ از connection مشترک یا تست محصور در transaction واحد استفاده نشود. در Django از TransactionTestCase یا harness معادل با commit واقعی استفاده شود.
- نقش اجرای عملیات همان role مجاز واقعی backend، nonowner و NOBYPASSRLS؛ نقش مشاهده قفل در connection سوم فقط privilege آزمایشی محدود لازم داشته باشد. مراقب تغییر نتایج با superuser/owner bypass باشید.
- زمان token و MFA deterministic و معتبر برای fixture؛ token خام در log چاپ نشود. role، PID، isolation و context presence ثبت شوند؛ secret/context حساس redact شود.

## هماهنگی و مشاهده؛ بدون sleep تصادفی

Harness از Event/Barrier در لایه آزمون استفاده کند؛ hookها فقط instrumentation تست، نه endpoint یا bypass تولید. هر عملیات واقعاً سرویس/adapter محصول را فراخوانی کند و transaction آن commit/rollback واقعی داشته باشد. اگر سرویس transaction خودش را می‌بندد، نقطه توقف قبل commit باید در harness معتبر قرار گیرد؛ patch عمومی محصول برای کنترل تست مجاز نیست.

برای schedule قطعی، worker اول پس از ورود به بخش بحرانی و اخذ قفل مشترک معتبر، event `lock_acquired` اعلام کند و قبل commit منتظر اجازه coordinator بماند. worker دوم آغاز شود؛ observer سوم با `pg_blocking_pids(second_pid)` و وضعیت wait/lock ثابت کند واقعاً پشت **worker اول** متوقف است. coordinator سپس commit اول را آزاد کند و نتیجه دوم را جمع‌آوری کند.

Barrier دوطرفه بعد از اخذ قفل قرار ندهید: worker دوم نمی‌تواند به آن برسد و deadlock مصنوعی ایجاد می‌شود. Barrier مشترک فقط پیش از عملیات رقابتی است. انتظارها bounded با deadline monotonic مثلاً ۱۰ ثانیه، connection/query timeout مناسب و cleanup قطعی باشند؛ نبود blocking مشاهده‌شده برای schedule موردنظر FAIL/آزمایش نامعتبر است، نه PASS حدسی. اگر backend راهکار optimistic دارد، به‌جای جعل lock witness، trace واقعی version/conflict/retry و ترتیب linearization آن با Architecture تعریف شود.

تمام commit/rollbackها و ترتیب completion با ساعت monotonic ثبت شوند. پس از پایان هر دو worker، oracle از connection سوم تازه و context مجاز خوانده شود؛ cache ORM یا snapshot worker شاهد نهایی نیست. آثار audit از مسیر مجاز و بدون bypass غیرواقعی بررسی شوند.

## سناریوها و oracle

| ID | schedule واقعی | نتیجه الزامی |
|---|---|---|
| PG-RACE-01 | R ابتدا قفل/بخش بحرانی، A واقعاً منتظر؛ R commit، سپس A | revoke موفق؛ accept همان دعوت رد؛ revoked_at ثبت؛ هیچ grant فعال برای capability هدف؛ یک audit مؤثر revoke، بدون audit پذیرش موفق |
| PG-RACE-02 | A ابتدا، R منتظر؛ A commit، سپس R | accept می‌تواند موفق شود؛ revoke سپس grant را غیرفعال می‌کند؛ پس از اتمام هر دو grant فعال صفر؛ دعوت accepted سابقه باقی می‌ماند، نه الزاماً revoked؛ audit پذیرش و revoke حاضر |
| PG-RACE-03 | fixture grant فعال + pending؛ هر دو ترتیب بالا | revoke هم grant و هم pending مربوط را پوشش دهد؛ grant قدیمی یا pending قدیمی پس از تکمیل revive نشوند |
| PG-RACE-04 | چند دعوت و multi-cap، هم‌زمان با دعوت‌های target U و Store A2/B1 | فقط دعوت‌های T/A1 حاوی capability لغوشده باطل؛ invite چندcapability طبق قرارداد موجود کامل باطل؛ unrelated rows و grants و auditها بی‌تغییر |
| PG-RACE-05 | failure injection پس از تغییر grant، پس از ابطال invite، هنگام audit؛ سپس retry | هر fault transaction را rollback کند؛ هیچ حالت نیمه‌کاره durable نشود؛ retry معتبر فقط اثر نهایی لازم و audit مؤثر ایجاد کند |
| PG-RACE-06 | دو revoke هم‌زمان برای همان T/A1/cap؛ سپس replay | یک تغییر مؤثر، audit مؤثر بدون duplicate بی‌اثر، timestamp لغو بی‌جهت بازنویسی نشود، هیچ invite فعال نشود |
| PG-RACE-07 | start barrier قبل عملیات، حداقل ۱۰۰ iteration با fixture/key تازه در هر بار؛ بدون ترتیب تحمیلی | هر نتیجه فقط معادل یکی از دو ترتیب معتبر 01/02 باشد؛ بعد از پایان هر دو مجوز قدیمی فعال نباشد؛ خطای غیرمنتظره/timeout به‌عنوان FAIL ثبت، نه retry مخفی |
| PG-RACE-08 | پس از پایان revoke، issue جدید با authorization معتبر و token جدید؛ سپس accept جدید و تلاش accept قدیمی | دعوت تازه مجاز و قابل پذیرش؛ دعوت قدیمی رد؛ revoke ممنوعیت دائمی دعوت ایجاد نکند |

برای PG-RACE-02 ممکن است API accept پیش از revoke موفق بوده باشد؛ oracle نهایی «grant فعال صفر پس از هر دو commit» است، نه الزام رد همه acceptها. این تفکیک مانع آزمون نادرست ترتیب‌ها می‌شود. اگر isolation واقعی SERIALIZABLE یا قفل/timeout موجب abort قانونی شد، retry محدود و سیاست خطا باید از baseline ثبت شود و تمام attempts/SQLSTATEها حفظ شوند؛ صرف خطا شدن یک worker موفقیت امنیتی/عملکردی نیست. پس از retry مجاز، oracle نهایی باید برقرار باشد.

## منفی‌آزمایی‌های همراه و محدودیت دامنه

- درخواست بدون context یا با tenant/store نامعتبر، manager فاقد حق، تلاش revoke حقوق مالک و MFA غایب/کهنه باید قبل اثر پایدار رد شود؛ اصل policy موجود حفظ گردد.
- RLS و composite FK با نقش واقعی جدا بررسی شوند؛ thread رقابتی با superuser نتیجه معتبر برای runtime نیست.
- failure در audit/notification نباید اثر DB نیمه‌کاره بدهد؛ notification خارجی باید از outbox معتبر پس از commit و با fixture محلی بررسی شود، نه ارسال واقعی.
- issue هم‌زمان با revoke یک تصمیم ordering جداست؛ این طرح ممنوعیت دائمی ایجاد نمی‌کند. قبل افزودن oracle سخت‌گیرانه‌تر از «دعوت‌های موجود در نقطه لغو»، semantics با Architecture روشن شود و در صورت تغییر قرارداد CR صادر شود.
- تست این طرح به‌تنهایی risk تغییر مجوز actor هم‌زمان با عملیات، identity revocation، pool-context leak و append-only audit را نمی‌بندد؛ suiteهای DB/Identity مجزا لازم‌اند.

## شواهد و معیار پذیرش

برای هر ID: source commit/hash، schema/migration revision، PostgreSQL/Django/driver versions، command واقعی، fixture ID بدون secret، role flags، isolation، دو PID مستقل، trace begin/lock/wait/commit/rollback، SQLSTATE و retry count، exit code، assertionها و snapshot نهایی scopeدار ثبت شود. اگر instrumentation/privilege مشاهده یا connection مستقل فراهم نیست، BLOCKED گزارش شود.

صفر violation در تمام scheduleها و تکرارها لازم است؛ هر violation FAIL و issue امنیتی. تنها با لاگ همین محیط PostgreSQL می‌توان GATE-PG-ACCEPT-REVOKE-CONCURRENCY را PASS کرد. **در S0-03 همه موارد بالا NOT_RUN / BLOCKED هستند.**
