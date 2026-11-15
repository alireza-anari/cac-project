"""Behavior-first: broken owner scoping/CSRF/CRUD/grounding must fail these."""
import secrets
from django.contrib.auth import get_user_model
from django.test import TestCase, Client


class JourneyTests(TestCase):
    def setUp(self):
        self.test_password = secrets.token_urlsafe(24)
        self.owner = get_user_model().objects.create_user('owner', password=self.test_password)
        self.other = get_user_model().objects.create_user('other', password=self.test_password)
        self.client = Client(HTTP_HOST='127.0.0.1')
        self.client.force_login(self.owner)

    def create_store(self):
        r = self.client.post('/stores/new/', {'name': 'فروشگاه نمونه', 'description': 'محلی'})
        self.assertEqual(r.status_code, 302)
        return r.url

    def test_login_required_and_real_login(self):
        guest = Client(HTTP_HOST='127.0.0.1')
        self.assertEqual(guest.get('/').status_code, 302)
        self.assertTrue(guest.login(username='owner', password=self.test_password))
        self.assertEqual(guest.get('/').status_code, 200)

    def test_store_and_product_crud_is_persistent(self):
        home = self.create_store()
        r = self.client.post(home + 'products/new/', {'name': 'قهوه', 'description': 'تازه',
                             'kind': 'product', 'price': '125000', 'available': 'on'})
        self.assertEqual(r.status_code, 302)
        self.assertContains(self.client.get(home), 'قهوه')
        from merchant.models import Product, Store
        p = Product.objects.get()
        self.client.post(home + f'products/{p.pk}/edit/', {'name': 'قهوه تازه',
                         'kind': 'service', 'description': 'ویرایش', 'price': '', 'available': ''})
        p.refresh_from_db()
        self.assertEqual(p.name, 'قهوه تازه')
        self.assertIsNone(p.price)
        self.assertFalse(p.available)
        self.client.post(home + 'edit/', {'name': 'نام تازه', 'description': 'ذخیره شد'})
        self.assertEqual(Store.objects.get().name, 'نام تازه')
        self.assertEqual(self.client.get(home + f'products/{p.pk}/delete/').status_code, 200)
        self.assertTrue(Product.objects.filter(pk=p.pk).exists())  # GET must not delete.
        self.client.post(home + f'products/{p.pk}/delete/')
        self.assertFalse(Product.objects.exists())

    def test_second_owner_cannot_read_or_mutate_objects(self):
        home = self.create_store()
        self.client.post(home+'products/new/', {'name': 'محرمانه', 'kind': 'product', 'description': ''})
        from merchant.models import Product
        p = Product.objects.get()
        self.client.force_login(self.other)
        for suffix in ('', 'edit/', 'assistant/', 'chat/', 'conversations/', 'settings/',
                       f'products/{p.pk}/edit/', f'products/{p.pk}/delete/', 'products/new/'):
            with self.subTest(suffix=suffix):
                self.assertEqual(self.client.get(home+suffix).status_code, 404)
                self.assertEqual(self.client.post(home+suffix, {'question': 'سلام', 'name': 'سرقت'}).status_code, 404)
        p.refresh_from_db()
        self.assertEqual(p.name, 'محرمانه')
        self.assertNotContains(self.client.get('/'), 'فروشگاه نمونه')

    def test_csrf_is_enforced_on_actual_routes(self):
        home = self.create_store()
        secure = Client(enforce_csrf_checks=True, HTTP_HOST='127.0.0.1')
        secure.force_login(self.owner)
        self.assertEqual(secure.post(home+'products/new/', {'name': 'بدون توکن'}).status_code, 403)
        secure.get(home+'products/new/')
        token = secure.cookies['csrftoken'].value
        r = secure.post(home+'products/new/', {'name': 'مجاز', 'description': '', 'kind': 'product',
                         'csrfmiddlewaretoken': token})
        self.assertEqual(r.status_code, 302)
        self.assertEqual(secure.post(home+'chat/', {'question': 'سلام'}).status_code, 403)
        self.assertEqual(secure.post('/login/', {'username': 'owner'}).status_code, 403)
        self.assertEqual(secure.post('/logout/').status_code, 403)

    def test_invalid_input_and_html_are_not_executed(self):
        home = self.create_store()
        r = self.client.post(home+'products/new/', {'name': 'a'*81, 'kind': 'product', 'price': '-1'})
        self.assertEqual(r.status_code, 200)
        from merchant.models import Product
        self.assertFalse(Product.objects.exists())
        self.client.post(home+'products/new/', {'name': '<script>alert(1)</script>', 'description': '<img src=x onerror=alert(1)>', 'kind': 'product'})
        r = self.client.get(home)
        self.assertNotContains(r, '<script>alert(1)</script>')
        self.assertContains(r, '&lt;script&gt;')

    def test_one_assistant_and_grounded_updated_chat(self):
        home = self.create_store()
        for name in ('یار فروشگاه', 'یار تازه'):
            self.assertEqual(self.client.post(home+'assistant/', {'name': name, 'greeting': 'خوش آمدید', 'tone': 'friendly'}).status_code, 302)
        from merchant.models import Assistant, Product, Exchange
        self.assertEqual(Assistant.objects.count(), 1)
        self.client.post(home+'products/new/', {'name': 'قهوه عربیکا', 'description': 'بسته تازه', 'kind': 'product', 'price': '125000', 'available': 'on'})
        r = self.client.post(home+'chat/', {'question': 'قیمت قهوه عربیکا چقدر است؟'}, follow=True)
        self.assertContains(r, '125,000')
        p = Product.objects.get()
        p.price = 99000
        p.save()
        self.client.post(home+'chat/', {'question': 'قیمت قهوه عربیکا'})
        self.assertIn('99,000', Exchange.objects.latest('id').answer)
        self.client.post(home+'chat/', {'question': 'هوای فردا چطور است؟'})
        self.assertIn('اطلاعاتی درباره این پرسش', Exchange.objects.latest('id').answer)
        self.assertContains(self.client.get(home+'chat/'), 'هوش مصنوعی واقعی متصل نیست')
        self.assertEqual(Assistant.objects.get().name, 'یار تازه')

    def test_no_public_routes_and_local_only(self):
        for url in ('/live/', '/api/chat/', '/widget/', '/register/', '/admin/'):
            self.assertEqual(self.client.get(url).status_code, 404)
        self.assertEqual(self.client.get('/', REMOTE_ADDR='192.0.2.10').status_code, 403)
        self.assertEqual(self.client.get('/', HTTP_HOST='public.example').status_code, 400)
