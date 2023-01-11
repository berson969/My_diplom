from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase, APIClient
from django.urls import reverse

from backend.models import User, Product, Shop
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
        pass

    def test_add_to_basket(self):
        pass

    def update_products_in_basket(self):
        pass

    def test_delete_from_basket(self):
        pass

    def test_get_basket(self):
        pass

    def test_get_user_orders(self):
        pass

    def test_make_order(self):
        pass

    def test_get_categories(self):
        pass
