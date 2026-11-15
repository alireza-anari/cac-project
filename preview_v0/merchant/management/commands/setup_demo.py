import secrets
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from merchant.models import Store, Product, Assistant


class Command(BaseCommand):
    help = 'Create a local demo account with a random password, never a fixed credential.'

    def add_arguments(self, parser):
        parser.add_argument('--reset-password', action='store_true')
        parser.add_argument('--seed', action='store_true')

    def handle(self, *args, **options):
        User = get_user_model()
        user = User.objects.filter(username='demo').first()
        if user and not options['reset_password']:
            self.stdout.write('حساب demo موجود است؛ برای رمز تصادفی تازه از --reset-password استفاده کنید.')
        else:
            password = secrets.token_urlsafe(18)
            if user is None:
                user = User.objects.create_user('demo', password=password)
            else:
                if user.is_staff or user.is_superuser:
                    raise CommandError('Demo must not be privileged.')
                user.set_password(password)
                user.save()
            self.stdout.write('فقط داده ساختگی؛ رمز را در Git یا ZIP نگذارید.\nنام کاربری: demo\nرمز تصادفی: '+password)
        if options['seed'] and not Store.objects.filter(owner=user).exists():
            store = Store.objects.create(owner=user, name='فروشگاه نمونه', description='داده ساختگی برای تجربه محلی')
            Product.objects.create(store=store, name='قهوه عربیکا', description='بسته نمونه ۲۵۰ گرمی', kind='product', price=125000, available=True)
            Product.objects.create(store=store, name='مشاوره خرید', description='خدمت نمونه', kind='service', available=False)
            Assistant.objects.create(store=store, name='یار فروشگاه', greeting='سلام! درباره محصولات نمونه بپرسید.', tone='friendly')
            self.stdout.write('فروشگاه نمونه و دو مورد ساختگی ساخته شد.')
