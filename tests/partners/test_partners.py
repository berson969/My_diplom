from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase, APIClient
from django.urls import reverse

from backend.models import User, Product, Shop
from tests.config import URL, FIRST_NAME, LAST_NAME, SUR_NAME, EMAIL_USER, PASSWORD_USER1, PASSWORD_USER2, COMPANY, \
    POSITION


class PartnerTests(APITestCase):
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

    def get_orders(self):
        self.create_user('shop')
        shop = Shop.objects.create(user_id=self.user.id)

    def test_update_price(self):
        self.create_user('shop')
        response = self.client.post(reverse('backend:partner-update'), data={'url': URL})
        count = Product.objects.all().count()
        self.assertEqual(count, 4)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['Status'], True)

    def test_update_price_without_url(self):
        self.create_user('shop')
        response = self.client.post(reverse('backend:partner-update'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['Status'], False)
        self.assertEqual(response.json()['Errors'], 'Не указаны все необходимые аргументы')

    def test_update_price_with_wrong_type(self):
        self.create_user('buyer')
        response = self.client.post(reverse('backend:partner-update'), data={'url': URL})
        # print('response', response.json())
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json()['Status'], False)
        self.assertEqual(response.json()['Error'], 'Только для магазинов')

    def test_get_partner_state(self):
        self.create_shop()
        response = self.client.get(reverse('backend:partner-state'), data={'url': URL})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['state'], True)
        self.assertEqual(response.json()['name'], 'Связной')

    def test_get_orders(self):
        self.get_orders()
        response = self.client.get(reverse('backend:partner-orders'), data={'url': URL})
        print('response', response.json())
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['state'], True)
        self.assertEqual(response.json()['name'], 'Связной')

    def test_update_partner_state(self):
        pass
