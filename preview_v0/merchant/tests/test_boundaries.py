import socket
import subprocess
import sys
from django.conf import settings
from django.db import IntegrityError, transaction
from merchant.models import Store, Product, Assistant, Exchange
from . import test_journey
from django.test import TestCase


class BoundaryTests(TestCase):
    setUp = test_journey.JourneyTests.setUp
    create_store = test_journey.JourneyTests.create_store
    # Reuse setup helpers without inheriting the journey test methods.
    def test_same_owner_cannot_switch_product_between_stores(self):
        home = self.create_store()
        other_store = Store.objects.create(owner=self.owner, name='فروشگاه دوم')
        p = Product.objects.create(store=other_store, name='فقط فروشگاه دوم', kind='product')
        for action in ('edit', 'delete'):
            for method in ('get', 'post'):
                r = getattr(self.client, method)(home+f'products/{p.pk}/{action}/', {'name': 'جابه‌جایی'})
                self.assertEqual(r.status_code, 404)
        self.assertNotContains(self.client.get(home), p.name)
        p.refresh_from_db()
        self.assertEqual(p.store_id, other_store.pk)

    def test_database_rejects_second_assistant(self):
        self.create_store()
        s = Store.objects.get()
        Assistant.objects.create(store=s, name='اول', greeting='سلام', tone='brief')
        with self.assertRaises(IntegrityError), transaction.atomic():
            Assistant.objects.create(store=s, name='دوم', greeting='سلام', tone='brief')
        self.assertEqual(Assistant.objects.filter(store=s).count(), 1)

    def test_editor_preserves_saved_assistant_fields(self):
        home = self.create_store()
        self.client.post(home+'assistant/', {'name': 'یار شخصی من', 'greeting': 'خوشامد سفارشی', 'tone': 'formal'})
        r = self.client.get(home+'assistant/')
        self.assertContains(r, 'value="یار شخصی من"')
        self.assertContains(r, 'خوشامد سفارشی')

    def test_saved_catalog_item_beyond_first_page_is_answered(self):
        home = self.create_store()
        s = Store.objects.get()
        Product.objects.bulk_create([Product(store=s, name=f'نمونه {i}', kind='product') for i in range(100)])
        Product.objects.create(store=s, name='مورد آخر', kind='product', price=41000)
        self.client.post(home+'assistant/', {'name': 'یار', 'greeting': 'سلام', 'tone': 'brief'})
        self.client.post(home+'chat/', {'question': 'قیمت مورد آخر'})
        self.assertIn('41,000', Exchange.objects.latest('id').answer)

    def test_specific_name_resolves_a_shorter_nested_product_name(self):
        home = self.create_store()
        s = Store.objects.get()
        Product.objects.create(store=s, name='قهوه', kind='product', price=1000)
        Product.objects.create(store=s, name='قهوه عربیکا', kind='product', price=125000)
        self.client.post(home+'assistant/', {'name': 'یار', 'greeting': 'سلام', 'tone': 'brief'})
        self.client.post(home+'chat/', {'question': 'قیمت قهوه عربیکا چقدر است؟'})
        answer = Exchange.objects.latest('id').answer
        self.assertIn('125,000', answer)
        self.assertNotIn('چند مورد پیدا شد', answer)

    def test_invalid_types_bounds_and_empty_questions_do_not_write(self):
        home = self.create_store()
        for price in ('NaN', 'Infinity', 'عدد', '-0.01', '999999999999999999'):
            r = self.client.post(home+'products/new/', {'name': 'محصول', 'kind': 'product', 'price': price})
            self.assertEqual(r.status_code, 200)
        self.assertEqual(Product.objects.count(), 0)
        self.client.post(home+'assistant/', {'name': 'دستیار', 'greeting': 'سلام', 'tone': 'brief'})
        for question in (' ', 'x'*501):
            self.assertEqual(self.client.post(home+'chat/', {'question': question}).status_code, 200)
        self.assertEqual(Exchange.objects.count(), 0)
        self.client.post(home+'assistant/', {'name': 'عوض نشود', 'greeting': 'سلام', 'tone': 'invented'})
        self.assertEqual(Assistant.objects.get().name, 'دستیار')

    def test_chat_and_assistant_text_escape_and_unknown_price(self):
        home = self.create_store()
        self.client.post(home+'assistant/', {'name': '<img src=x onerror=alert(1)>', 'greeting': '<script>alert(1)</script>', 'tone': 'formal'})
        Product.objects.create(store=Store.objects.get(), name='کالای نمونه', kind='product', available=False)
        self.client.post(home+'chat/', {'question': 'قیمت کالای نمونه <script>alert(2)</script>'})
        r = self.client.get(home+'chat/')
        self.assertNotContains(r, '<script>alert(')
        self.assertNotContains(r, '<img src=x')
        self.assertContains(r, '&lt;script&gt;')
        self.assertContains(r, 'قیمت ثبت نشده است')
        self.assertContains(r, 'فعلاً در دسترس نیست')

    def test_all_write_routes_require_csrf(self):
        from django.test import Client
        home = self.create_store()
        p = Product.objects.create(store=Store.objects.get(), name='باقی بماند', kind='product')
        c = Client(enforce_csrf_checks=True, HTTP_HOST='127.0.0.1')
        c.force_login(self.owner)
        for route in ('/stores/new/', home+'edit/', home+'assistant/', home+'products/new/',
                      home+f'products/{p.pk}/edit/', home+f'products/{p.pk}/delete/', home+'chat/'):
            self.assertEqual(c.post(route, {'name': 'بدون توکن'}).status_code, 403)
        self.assertTrue(Product.objects.filter(pk=p.pk).exists())

    def test_no_outbound_connect_and_dns_at_runtime(self):
        from config.network import install
        install()
        with socket.socket() as sock, self.assertRaisesRegex(RuntimeError, 'Outbound'):
            sock.connect(('203.0.113.1', 443))  # audit rejects BEFORE an actual connect.
        with self.assertRaisesRegex(RuntimeError, 'External DNS'):
            socket.getaddrinfo('no-runtime-egress.example', 443)
        home = self.create_store()
        self.client.post(home+'assistant/', {'name': 'محلی', 'greeting': 'سلام', 'tone': 'brief'})
        self.assertEqual(self.client.post(home+'chat/', {'question': 'چه محصولاتی دارید؟'}).status_code, 302)

    def test_public_bind_is_rejected_before_server_start(self):
        result = subprocess.run([sys.executable, 'manage.py', 'runserver', '0.0.0.0:8000', '--noreload'],
                                cwd=settings.BASE_DIR, capture_output=True, text=True, timeout=10)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('127.0.0.1', result.stderr)
