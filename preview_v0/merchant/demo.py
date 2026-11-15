"""Deterministic retrieval of saved local fields. No provider, inference or HTTP."""
import re


def normalized(text):
    return re.sub(r'[^\w\s]', ' ', text.casefold().replace('ي', 'ی').replace('ك', 'ک')).strip()


def reply(store, assistant, question):
    q = normalized(question)
    products = list(store.products.all())
    if q in ('سلام', 'درود', 'سلام خوبی'):
        return assistant.greeting
    if any(x in q for x in ('چه محصولاتی', 'محصولات دارید', 'لیست', 'فهرست', 'چه خدماتی', 'چه دارید')):
        if not products:
            return 'هنوز محصول یا خدمتی در این فروشگاه ثبت نشده است.'
        heading = '۲۰ مورد نخست محصولات و خدمات:\n' if len(products) > 20 else 'محصولات و خدمات ثبت‌شده:\n'
        return heading + '\n'.join('• '+p.name for p in products[:20]) + '\nبرای دیدن جزئیات، نام دقیق را بنویسید.'
    exact = [p for p in products if normalized(p.name) and normalized(p.name) in q]
    if exact:
        longest = max((normalized(p.name) for p in exact), key=len)
        if all(normalized(p.name) in longest for p in exact):
            exact = [p for p in exact if normalized(p.name) == longest]
    matches = exact or [p for p in products if any(len(w) >= 3 and w in q.split() for w in normalized(p.name).split())]
    if len(matches) > 1:
        return 'چند مورد پیدا شد؛ لطفاً نام دقیق را بنویسید:\n' + '\n'.join('• '+p.name for p in matches[:10])
    if not matches:
        return 'اطلاعاتی درباره این پرسش در داده‌های ثبت‌شده ندارم. نام محصول یا خدمت را بنویسید یا فهرست محصولات را بخواهید.'
    p = matches[0]
    price = f'{p.price:,.2f}'.rstrip('0').rstrip('.')+' تومان' if p.price is not None else 'قیمت ثبت نشده است'
    lines = [p.name, 'قیمت: '+price, 'وضعیت: '+('در دسترس' if p.available else 'فعلاً در دسترس نیست')]
    if assistant.tone != 'brief' and p.description:
        lines.append(p.description)
    prefix = {'friendly': 'حتماً! این اطلاعات ثبت‌شده فروشگاه است:\n',
              'formal': 'اطلاعات ثبت‌شده به شرح زیر است:\n', 'brief': ''}[assistant.tone]
    return prefix+'\n'.join(lines)
