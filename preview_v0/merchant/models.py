from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models


class Store(models.Model):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    name = models.CharField('نام فروشگاه', max_length=80)
    description = models.TextField('درباره فروشگاه', max_length=1200, blank=True)

    def get_absolute_url(self):
        return f'/s/{self.pk}/'


class Product(models.Model):
    store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name='products')
    name = models.CharField('نام محصول یا خدمت', max_length=80)
    description = models.TextField('توضیحات', max_length=1200, blank=True)
    kind = models.CharField('نوع', max_length=10, choices=[('product', 'محصول'), ('service', 'خدمت')])
    price = models.DecimalField('قیمت به تومان (اختیاری)', max_digits=12, decimal_places=2,
                                blank=True, null=True, validators=[MinValueValidator(0)])
    available = models.BooleanField('در دسترس است', default=True)

    class Meta:
        ordering = ['id']
        constraints = [models.CheckConstraint(condition=models.Q(price__gte=0) | models.Q(price__isnull=True), name='preview_nonnegative_price')]


class Assistant(models.Model):
    store = models.OneToOneField(Store, on_delete=models.CASCADE, related_name='assistant')
    name = models.CharField('نام دستیار', max_length=60)
    greeting = models.CharField('پیام خوشامد', max_length=300)
    tone = models.CharField('سبک پاسخ', max_length=10,
                           choices=[('friendly', 'صمیمی'), ('formal', 'رسمی'), ('brief', 'کوتاه')])


class Exchange(models.Model):
    store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name='exchanges')
    question = models.CharField(max_length=500)
    answer = models.TextField(max_length=8000)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['id']
