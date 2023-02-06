from rest_framework.test import APITestCase, APIClient
from django.urls import reverse

from backend.models import OrderItem, Order
from tests.conftest import create_shop, add_orders, add_contacts, get_orders


class ShopTests(APITestCase):
    def setUp(self) -> None:
        self.client = APIClient()

    def test_list_shops(self):
        create_shop(self.client)
        response = self.client.get(reverse('backend:shops'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 4)

    def test_find_product(self):
        create_shop(self.client)
        response = self.client.get(reverse('backend:products'), shop_id=1, category_id=224)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 4)

    def test_find_product_without_search(self):
        create_shop(self.client)
        response = self.client.get(reverse('backend:products'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 4)

    def test_add_to_basket(self):
        product_info, user = create_shop(self.client)
        data = dict(items=f'[{{"product_info": {product_info.id}, "quantity": 1}},'
                          f'{{"product_info": {product_info.id + 1}, "quantity": 1}}]'
                    )
        response = self.client.post(reverse('backend:basket'), data=data)
        order_items = OrderItem.objects.select_related('order').filter(order__user_id=user.id).all()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['Создано объектов'], 2)
        self.assertEqual(len(order_items), 2)

    def test_update_products_in_basket(self):
        client, user = add_orders(self.client)
        order_item = OrderItem.objects.select_related('order').filter(order__state='basket',
                                                                      order__user_id=user.id).first()
        data = dict(items=f'[{{"id": {order_item.id}, "quantity": 5}}]')
        response = client.put(reverse('backend:basket'), data=data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['Обновлено объектов'], 1)

    def test_delete_from_basket(self):
        client, user = add_orders(self.client)
        order_item = OrderItem.objects.select_related('order').filter(order__state='basket',
                                                                      order__user_id=user.id).first()
        data = dict(items=f'{order_item.id},{order_item.id+1}')
        response = client.delete(reverse('backend:basket'), data=data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['Status'], True)
        self.assertEqual(response.json()['Удалено объектов'], 2)

    def test_get_basket(self):
        client, user = add_orders(self.client)
        response = client.get(reverse('backend:basket'))
        order = Order.objects.filter(user=user.id).first()
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.json()[0]['ordered_items'], list)
        self.assertEqual(response.json()[0]['id'], order.id)

    def test_make_order(self):
        client, user = add_orders(self.client)
        data = {
            'id': Order.objects.filter(user=user.id, state='basket').first().id,
            'contact': add_contacts(client).id
        }
        response = client.post(reverse('backend:order'), data=data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['Status'], True)

    def test_get_user_orders(self):
        order, user = get_orders(self.client)
        response = self.client.get(reverse('backend:order'))
        order = Order.objects.filter(user=user.id).first()
        # print(response.json())
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.json()[0]['ordered_items'], list)
        self.assertEqual(response.json()[0]['id'], order.id)

    def test_get_categories(self):
        create_shop(self.client)
        response = self.client.get(reverse('backend:categories'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['count'], 3)
        self.assertIsInstance(response.json()['results'], list)
