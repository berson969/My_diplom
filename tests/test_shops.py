from random import randint
from pprint import pprint

from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase, APIClient
from django.urls import reverse

from backend.models import User, OrderItem, ProductInfo, Contact, Order
from tests.config import URL, FIRST_NAME, LAST_NAME, SUR_NAME, EMAIL_USER, PASSWORD_USER1, PASSWORD_USER2, COMPANY, \
    POSITION, CITY, STREET, PHONE


class ShopTests(APITestCase):
    def setUp(self) -> None:
        self.data = {
            'first_name': FIRST_NAME,
            'last_name': LAST_NAME,
            'surname': SUR_NAME,
            'email': EMAIL_USER,
            'password1': PASSWORD_USER1,
            'password2': PASSWORD_USER2,
            'company': COMPANY,
            'position': POSITION,
        }
        self.contact = {
            'city': CITY,
            'street': STREET,
            'phone': PHONE,
        }

    def create_user(self, type):
        self.user = User.objects.create(email=f"user_{randint(10000, 99999)}@admin.ru", type=type, is_active=True)
        token = Token.objects.create(key=f"token_{randint(100000, 999999)}", user_id=self.user.id)
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

    def create_shop(self):
        self.create_user('shop')
        self.client.post(reverse('backend:partner-update'), data={'url': URL})
        return ProductInfo.objects.first()

    def add_to_basket(self):
        product_info = self.create_shop()
        data = dict(items=f'[{{"product_info": {product_info.id}, "quantity": 2}},'
                          f' {{"product_info": {product_info.id+1}, "quantity": 3}}]'
                    )
        self.client.post(reverse('backend:basket'), data=data)
        self.order = Order.objects.filter(user=self.user.id).first()
        return OrderItem.objects.first()

    def add_contact(self):
        self.contact.update(user=self.user.id)
        self.client.post(reverse('backend:user-contact'), data=self.contact)
        return Contact.objects.first()

    def get_orders(self):
        product_info = self.create_shop()
        data = dict(items=f'[{{"product_info": {product_info.id}, "quantity": 2}},'
                          f' {{"product_info": {product_info.id + 1}, "quantity": 3}}]'
                    )
        self.create_user('buyer')
        self.client.post(reverse('backend:basket'), data=data)
        contact = self.add_contact()
        self.order = Order.objects.filter(user=self.user.id).first()
        self.client.post(reverse('backend:order'), {'id': self.order.id, 'contact': contact.id})

    def test_list_shops(self):
        self.create_shop()
        response = self.client.get(reverse('backend:shops'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 4)

    def test_find_product(self):
        self.create_shop()
        response = self.client.get(reverse('backend:products'), shop_id=1, category_id=224)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 4)

    def test_find_product_without_search(self):
        self.create_shop()
        response = self.client.get(reverse('backend:products'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 4)

    def test_add_to_basket(self):
        product_info = self.create_shop()
        data = dict(items=f'[{{"product_info": {product_info.id}, "quantity": 1}},'
                          f'{{"product_info": {product_info.id+1}, "quantity": 1}}]'
                    )
        response = self.client.post(reverse('backend:basket'), data=data)
        order_items = OrderItem.objects.all()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['Создано объектов'], 2)
        self.assertEqual(len(order_items), 2)

    def test_update_products_in_basket(self):
        order_items = self.add_to_basket()
        data = dict(items=f'[{{"id": {order_items.id}, "quantity": 5}}]')
        response = self.client.put(reverse('backend:basket'), data=data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['Обновлено объектов'], 1)

    def test_delete_from_basket(self):
        order_items = self.add_to_basket()
        data = dict(items=f'{order_items.id},{order_items.id+1}')
        response = self.client.delete(reverse('backend:basket'), data=data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['Status'], True)
        self.assertEqual(response.json()['Удалено объектов'], 2)

    def test_get_basket(self):
        self.add_to_basket()
        response = self.client.get(reverse('backend:basket'))
        # pprint(response.json())
        order = Order.objects.filter(user=self.user.id).first()
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.json()[0]['ordered_items'], list)
        self.assertEqual(response.json()[0]['id'], order.id)

    def test_make_order(self):
        self.add_to_basket()
        contact = self.add_contact()
        response = self.client.post(reverse('backend:order'), {'id': self.order.id, 'contact': contact.id})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['Status'], True)

    def test_get_user_orders(self):
        self.get_orders()
        response = self.client.get(reverse('backend:order'))
        order = Order.objects.filter(user=self.user.id).first()
        # pprint(response.json())
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.json()[0]['ordered_items'], list)
        self.assertEqual(response.json()[0]['id'], order.id)

    def test_get_categories(self):
        self.create_shop()
        response = self.client.get(reverse('backend:categories'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['count'], 3)
        self.assertIsInstance(response.json()['results'], list)
