from rest_framework.test import APITestCase, APIClient
from django.urls import reverse

from backend.models import Order, OrderItem
from tests.conftest import get_orders, change_to_confirmed, change_to_assembled, change_to_sent, get_fault_orders


class StorageAdminTests(APITestCase):

    def setUp(self) -> None:
        self.client = APIClient()

    def test_change_order(self):
        order, user = get_orders(self.client)
        response = self.client.put(reverse('backend:order'), {'id': order.id})
        # print(response.json())
        order = Order.objects.filter(user=user.id).first()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['Status'], True)
        self.assertEqual(order.state, 'confirmed')

    def test_change_to_assembled(self):
        order, user = change_to_confirmed(self.client)
        response = self.client.post(reverse('backend:storage'), {'id': order.id})
        # print(response.json())
        order = Order.objects.filter(user=user.id).first()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['Status'], True)
        self.assertEqual(order.state, 'assembled')

    def test_change_to_sent(self):
        order, user = change_to_assembled(self.client)
        response = self.client.put(reverse('backend:storage'), {'id': order.id})
        state = Order.objects.filter(id=order.id).first().state
        product = OrderItem.objects.select_related('product_info').filter(order_id=order.id).first()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['Status'], True)
        self.assertEqual(state, 'sent')
        self.assertEqual(product.product_info.quantity, 12)

    def test_change_to_delivered(self):
        order, user = change_to_sent(self.client)
        response = self.client.patch(reverse('backend:storage'), {'id': order.id})
        # print(response.json())
        order = Order.objects.filter(user=user.id).first()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['Status'], True)
        self.assertEqual(order.state, 'delivered')

    def test_delete_from_sent(self):
        order, user = change_to_sent(self.client)
        response = self.client.delete(reverse('backend:storage'), {'id': order.id})
        # print(response.json())
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['Status'], False)
        self.assertEqual(response.json()['Errors'], 'Данный заказ нельзя отменить')

    def test_delete_from_confirmed(self):
        order, user = change_to_confirmed(self.client)
        response = self.client.delete(reverse('backend:storage'), {'id': order.id})
        order = Order.objects.filter(user=user.id, id=order.id).first()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['Status'], True)
        self.assertEqual(order.state, 'canceled')

    def test_confirm_with_big_quantity(self):
        order, user = get_fault_orders(self.client)
        response = self.client.put(reverse('backend:order'), {'id': order.id})
        # print(response.json())
        order = Order.objects.filter(user=user.id).first()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['Status'], False)
        self.assertEqual(order.state, 'new')
