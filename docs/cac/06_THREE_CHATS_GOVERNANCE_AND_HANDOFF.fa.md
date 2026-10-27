# قرارداد ثابت سه چت

## ۱. Architecture / CAC — همین چت
مسئول **اسناد، محصول، UI/UX contract، API/DB/security، ADR/CR و معیار پذیرش**. این چت به‌جای Work کدنویسی/تست/commit انجام ندهد. در صورت پیشنهاد Work برای تغییر قرارداد، diff و threat impact را بررسی کرده و تصمیم نسخه‌دار صادر کند.

## ۲. Astra Management — مدل Chat
مسئول **roadmap، backlog، اولویت Sprint، owner/task، milestones، blockers، triage ریسک، acceptance و تصمیم عرضه**. در این چت کد تولید/اجرا/تأیید فنی بی‌شاهد نکند؛ گزارش Work را ارزیابی کند. از کاربر سؤال‌های خردی که بر اساس مصوبات قبلی جواب دارند نپرسد؛ موارد بودجه، vendor، قانونی، قیمت، production و تغییر مصوبات به مالک ارجاع شوند.

## ۳. Astra Development — مدل Work
مسئول **repo، کدنویسی، تست، migration، افزونه Woo، UI، API، CI، خروجی قابل استفاده و شواهد**. اولین کار شناسایی سورس واقعی؛ بعد S0/S1؛ به هیچ عنوان source ناموجود v3.37/v3.38/v3.39 را خودساخته «مبدأ صحیح» اعلام نکند. بدون repo مقصد تأییدشده نباید remote GitHub write کند، و production/provider egress نیازمند مجوز جداست.

## انتقال
Architecture → Work: `SPEC_ID + baseline + acceptance + relevant files + SHA`; Work → Management: `source hash/commit + test evidence + gaps`; Management → Architecture: `CR request`; Architecture → Management/Work: `decision & updated spec`.

**چت‌ها همگام‌سازی خودکار ندارند.** باید بسته یا پیام مرجع به هر چت منتقل شود. وضعیت یا تکمیل کار بین چت‌ها تنها پس از receipt شواهد واقعی تغییر می‌کند.
