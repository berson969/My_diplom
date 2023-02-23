from celery import Celery

from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase, APIClient
from django.urls import reverse
from django.db.models import F

from backend.models import User, Product, Shop, Order
from tests.config_test import URL, PASSWORD_USER1, REDIS_URL
from tests.conftest import login_user, create_shop, get_orders
from backend.tasks import get_price


class PartnerTests(APITestCase):
    def setUp(self) -> None:
        self.client = APIClient()

    # app = Celery('netology_pd_diplom', broker=f'{REDIS_URL}/1', backend=f'{REDIS_URL}/1')

    # def test_update_price(self):
    #     self.client, user = login_user(self.client)
    #     response = self.client.post(reverse('backend:partner-update'), data={'url': URL})
    #     print(response.json())
    #     count = Product.objects.all().count()
    #     self.assertEqual(count, 4)
    #     self.assertEqual(response.status_code, 200)
    #     self.assertEqual(response.json()['Status'], True)
    #
    # def test_get_price(self):
    #     self.client, user = login_user(self.client)
    #     job_params = {'url': URL, 'user_id': user.id}
    #     response = get_price.delay(job_params)
    #     print(response.get())

    def test_update_price_without_url(self):
        self.client, user = login_user(self.client)
        response = self.client.post(reverse('backend:partner-update'))
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()['Status'], False)
        self.assertEqual(response.json()['Errors'], 'Не указаны все необходимые аргументы')

    def test_update_price_with_wrong_type(self):
        self.client, user = login_user(self.client)
        User.objects.filter(id=user.id).update(type='buyer')
        response = self.client.post(reverse('backend:partner-update'), data={'url': URL})
        # print('response', response.json())
        self.assertEqual(response.status_code, 405)
        self.assertEqual(response.json()['Status'], False)
        self.assertEqual(response.json()['Error'], 'Только для магазинов')

    def test_get_partner_state(self):
        create_shop(self.client)
        response = self.client.get(reverse('backend:partner-state'), data={'url': URL})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['state'], True)
        self.assertEqual(response.json()['name'], 'Связной')

    def test_update_partner_state(self):
        product, user = create_shop(self.client)
        response = self.client.post(reverse('backend:partner-state'), {'state': False})
        shop = Shop.objects.filter(user_id=user.id).first()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['Status'], True)
        self.assertEqual(shop.state, False)

    def test_get_orders(self):
        order, user = get_orders(self.client)
        shop = Order.objects.filter(id=order.id)\
            .prefetch_related('ordered_items__product_info__shop__user').annotate(
            email=F('ordered_items__product_info__shop__user__email')).first()
        response = self.client.post(reverse('backend:user-login'), {
            'email': shop.email,
            'password': PASSWORD_USER1
        })
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + response.json()['Token'])
        response = self.client.get(reverse('backend:partner-orders'))
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.json()[0]['ordered_items'], list)
        self.assertEqual(response.json()[0]['id'], order.id)
