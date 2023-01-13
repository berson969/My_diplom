import json

from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase, APIClient
from django.urls import reverse

from backend.models import User, Product, Shop, OrderItem
from tests.config import URL, FIRST_NAME, LAST_NAME, SUR_NAME, EMAIL_USER, PASSWORD_USER1, PASSWORD_USER2, COMPANY, \
    POSITION


class ShopTests(APITestCase):
    def setUp(self) -> None:
        pass
    #     self.data = {
    #         'first_name': FIRST_NAME,
    #         'last_name': LAST_NAME,
    #         'surname': SUR_NAME,
    #         'email': EMAIL_USER,
    #         'password1': PASSWORD_USER1,
    #         'password2': PASSWORD_USER2,
    #         'company': COMPANY,
    #         'position': POSITION,
    #     }

    def create_user(self, type):
        self.user = User.objects.create(email=EMAIL_USER, type=type, is_active=True)
        token = Token.objects.create(key=PASSWORD_USER1, user_id=self.user.id)
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

    def create_shop(self):
        self.create_user('shop')
        response = self.client.post(reverse('backend:partner-update'), data={'url': URL})

    def add_to_basket(self):
        self.create_shop()
        data = dict(items='[{"product_info": 2, "quantity": 2}, {"product_info": 3, "quantity": 3}]')
        response = self.client.post(reverse('backend:basket'), data=data)
        order_items = OrderItem.objects.all()
        print(order_items)
        print(response.json())
    # def get_orders(self):
    #     self.create_user('shop')
    #     shop = Shop.objects.create(user_id=self.user.id)

    def test_list_shops(self):
        self.create_shop()
        response = self.client.get(reverse('backend:shops'))
        # print('shops', response.json())
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
        self.create_shop()
        data = dict(items='[{"product_info": 2, "quantity": 2}, {"product_info": 3, "quantity": 3}]')
        response = self.client.post(reverse('backend:basket'), data=data)
        order_items = OrderItem.objects.all()
        # print(order_items)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['Создано объектов'], 2)
        self.assertEqual(len(order_items), 2)

    # def test_update_products_in_basket(self):
    #     self.add_to_basket()
    #     data = dict(items='[{"id": 2, "quantity": 5},]')
    #     response = self.client.put(reverse('backend:basket'), data=data)
    #     order_items = OrderItem.objects.all()
    #     # print(order_items)
    #     # print(response.json())
    #     self.assertEqual(response.status_code, 200)
    #     self.assertEqual(response.json()['Обновлено объектов'], 1)
    #
    # def test_delete_from_basket(self):
    #     self.add_to_basket()
    #     data = dict(items='2,3')
    #     order_items = OrderItem.objects.all()
    #     # print(order_items)
    #     response = self.client.delete(reverse('backend:basket'), data=data)
    #     self.assertEqual(response.status_code, 200)
    #     self.assertEqual(response.json()['Status'], True)
    #     self.assertEqual(response.json()['Удалено объектов'], 1)

    def test_get_basket(self):
        pass

    def test_get_user_orders(self):
        self.add_to_basket()
        response = self.client.get(reverse('backend:order'))
        print('get_order', response.json())
        self.assertEqual(response.status_code, 200)
        # self.assertEqual(response.json()['count'], 3)
        # self.assertIsInstance(response.json()['results'], list)

    def test_make_order(self):

        pass

    def test_get_categories(self):
        self.create_shop()
        response = self.client.get(reverse('backend:categories'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['count'], 3)
        self.assertIsInstance(response.json()['results'], list)