from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from tests.conftest import create_shop, add_orders

from backend.models import OrderItem, Order


class BasketViewSetTest(APITestCase):

    def setUp(self) -> None:
        self.client = APIClient()

    def test_create_basket(self):
        product_info, user = create_shop(self.client)
        data = dict(items=f'[{{"product_info": {product_info.id}, "quantity": 1}},'
                          f'{{"product_info": {product_info.id + 1}, "quantity": 1}}]'
                    )
        response = self.client.post(reverse('viewset-list'), data=data)
        order_items = OrderItem.objects.select_related('order').filter(order__user_id=user.id).all()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['Создано объектов'], 2)
        self.assertEqual(len(order_items), 2)

    def test_update_basket(self):
        client, user = add_orders(self.client)
        order_item = OrderItem.objects.select_related('order').filter(order__state='basket',
                                                                      order__user_id=user.id).first()
        data = dict(items=f'[{{"id": {order_item.id}, "quantity": 5}}]')
        response = client.put(reverse('viewset-update-basket'), data=data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['Обновлено объектов'], 1)

    def test_delete_basket(self):
        client, user = add_orders(self.client)
        order_item = OrderItem.objects.select_related('order').filter(order__state='basket',
                                                                      order__user_id=user.id).first()
        data = dict(items=f'{order_item.id},{order_item.id + 1}')
        response = client.delete(reverse('viewset-destroy-product'), data=data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['Status'], True)
        self.assertEqual(response.json()['Удалено объектов'], 2)

    def test_list_basket(self):
        client, user = add_orders(self.client)
        response = client.get(reverse('viewset-list'))
        order = Order.objects.filter(user=user.id).first()
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.json()[0]['ordered_items'], list)
        self.assertEqual(response.json()[0]['id'], order.id)
