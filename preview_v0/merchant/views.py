from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods
from django.http import HttpResponseNotAllowed
from .forms import StoreForm, ProductForm, AssistantForm, QuestionForm
from .models import Store, Product, Assistant, Exchange
from .demo import reply


def owned(request, store_id):
    return get_object_or_404(Store, pk=store_id, owner=request.user)


def context(store, page, **extra):
    return {'store': store, 'page': page, **extra}


@login_required
@require_http_methods(['GET'])
def index(request):
    return render(request, 'merchant/index.html', {'stores': Store.objects.filter(owner=request.user), 'page': 'overview'})


@login_required
@require_http_methods(['GET', 'POST'])
def store_form(request, store_id=None):
    store = owned(request, store_id) if store_id is not None else None
    form = StoreForm(request.POST if request.method == 'POST' else None, instance=store)
    if request.method == 'POST' and form.is_valid():
        record = form.save(commit=False)
        record.owner = request.user
        record.save()
        messages.success(request, 'اطلاعات فروشگاه ذخیره شد.')
        return redirect(record)
    return render(request, 'merchant/form.html', context(store, 'settings', form=form, title='ویرایش فروشگاه' if store else 'فروشگاه آزمایشی تازه', back=store.get_absolute_url() if store else '/'))


@login_required
def overview(request, store_id):
    store = owned(request, store_id)
    if request.method != 'GET':
        return HttpResponseNotAllowed(['GET'])
    return render(request, 'merchant/overview.html', context(store, 'overview', products=store.products.all(), configured=Assistant.objects.filter(store=store).exists()))


@login_required
@require_http_methods(['GET', 'POST'])
def product_form(request, store_id, product_id=None):
    store = owned(request, store_id)
    product = get_object_or_404(Product, pk=product_id, store=store) if product_id is not None else None
    form = ProductForm(request.POST if request.method == 'POST' else None, instance=product)
    if request.method == 'POST' and form.is_valid():
        record = form.save(commit=False)
        record.store = store
        record.save()
        messages.success(request, 'محصول یا خدمت ذخیره شد؛ پاسخ جدید گفتگو از همین اطلاعات استفاده می‌کند.')
        return redirect(store)
    return render(request, 'merchant/form.html', context(store, 'overview', form=form, title='ویرایش محصول یا خدمت' if product else 'افزودن محصول یا خدمت', back=store.get_absolute_url()))


@login_required
@require_http_methods(['GET', 'POST'])
def product_delete(request, store_id, product_id):
    store = owned(request, store_id)
    product = get_object_or_404(Product, pk=product_id, store=store)
    if request.method == 'POST':
        product.delete()
        messages.success(request, 'مورد انتخاب‌شده حذف شد.')
        return redirect(store)
    return render(request, 'merchant/delete.html', context(store, 'overview', product=product))


@login_required
@require_http_methods(['GET', 'POST'])
def assistant(request, store_id):
    store = owned(request, store_id)
    record = Assistant.objects.filter(store=store).first()
    form = AssistantForm(request.POST if request.method == 'POST' else None, instance=record,
                         initial=None if record else {'name': 'یار فروشگاه', 'greeting': 'سلام! درباره محصولات و خدمات ثبت‌شده بپرسید.', 'tone': 'friendly'})
    if request.method == 'POST' and form.is_valid():
        # Serialize local updates; OneToOne additionally prevents duplicate rows.
        with transaction.atomic():
            Assistant.objects.update_or_create(store=store, defaults=form.cleaned_data)
        messages.success(request, 'تنظیمات دستیار خصوصی ذخیره شد.')
        return redirect('assistant', store_id=store.pk)
    return render(request, 'merchant/assistant.html', context(store, 'assistant', form=form, configured=record is not None))


@login_required
@require_http_methods(['GET', 'POST'])
def chat(request, store_id):
    store = owned(request, store_id)
    assistant = Assistant.objects.filter(store=store).first()
    if assistant is None:
        messages.info(request, 'ابتدا دستیار خصوصی را ذخیره کنید.')
        return redirect('assistant', store_id=store.pk)
    form = QuestionForm(request.POST if request.method == 'POST' else None)
    if request.method == 'POST' and form.is_valid():
        question = form.cleaned_data['question']
        Exchange.objects.create(store=store, question=question, answer=reply(store, assistant, question))
        return redirect('chat', store_id=store.pk)
    exchanges = list(store.exchanges.order_by('-id')[:50])[::-1]
    return render(request, 'merchant/chat.html', context(store, 'conversations', assistant=assistant, form=form, exchanges=exchanges))


@login_required
def conversations(request, store_id):
    store = owned(request, store_id)
    if request.method != 'GET':
        return HttpResponseNotAllowed(['GET'])
    return render(request, 'merchant/conversations.html', context(store, 'conversations', exchanges=store.exchanges.order_by('-id')[:100]))


@login_required
def settings(request, store_id):
    store = owned(request, store_id)
    if request.method != 'GET':
        return HttpResponseNotAllowed(['GET'])
    return render(request, 'merchant/settings.html', context(store, 'settings'))
