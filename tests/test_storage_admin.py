from random import randint

from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase, APIClient
from django.urls import reverse

from backend.models import User, ProductInfo, Order, OrderItem, Contact
from tests.config import URL, CITY, STREET, PHONE


class StorageAdminTests(APITestCase):

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
                          f' {{"product_info": {product_info.id + 1}, "quantity": 3}}]'
                    )
        self.client.post(reverse('backend:basket'), data=data)
        self.order = Order.objects.filter(user=self.user.id).first()
        return OrderItem.objects.first()

    def add_contact(self):
        self.contact = {
            'city': CITY,
            'street': STREET,
            'phone': PHONE,
        }
        self.contact.update(user=self.user.id)
        self.client.post(reverse('backend:user-contact'), data=self.contact)
        return Contact.objects.first()

    def get_orders(self):
        product_info = self.create_shop()
        data = dict(items=f'[{{"product_info": {product_info.id}, "quantity": 14}},'
                          f' {{"product_info": {product_info.id + 1}, "quantity": 3}}]'
                    )
        self.create_user('buyer')
        self.client.post(reverse('backend:basket'), data=data)
        contact = self.add_contact()
        self.order = Order.objects.filter(user=self.user.id).first()
        self.client.post(reverse('backend:order'), {'id': self.order.id, 'contact': contact.id})

    def get_fault_orders(self):
        product_info = self.create_shop()
        data = dict(items=f'[{{"product_info": {product_info.id}, "quantity": 100}},'
                          f' {{"product_info": {product_info.id + 1}, "quantity": 1}}]'
                    )
        self.create_user('buyer')
        self.client.post(reverse('backend:basket'), data=data)
        contact = self.add_contact()
        self.order = Order.objects.filter(user=self.user.id).first()
        self.client.post(reverse('backend:order'), {'id': self.order.id, 'contact': contact.id})

    def change_to_confirmed(self):
        self.get_orders()
        self.client.put(reverse('backend:order'), {'id': self.order.id})

    def change_to_assembled(self):
        self.change_to_confirmed()
        self.client.post(reverse('backend:storage'), {'id': self.order.id})

    def change_to_sent(self):
        self.change_to_assembled()
        self.client.patch(reverse('backend:storage'), {'id': self.order.id})

    def test_change_order(self):
        self.get_orders()
        response = self.client.put(reverse('backend:order'), {'id': self.order.id})
        # print(response.json())
        order = Order.objects.filter(user=self.user.id).first()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['Status'], True)
        self.assertEqual(order.state, 'confirmed')

    def test_change_to_assembled(self):
        self.change_to_confirmed()
        response = self.client.post(reverse('backend:storage'), {'id': self.order.id})
        # print(response.json())
        order = Order.objects.filter(user=self.user.id).first()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['Status'], True)
        self.assertEqual(order.state, 'assembled')

    def test_change_to_sent(self):
        self.change_to_assembled()
        response = self.client.put(reverse('backend:storage'), {'id': self.order.id})
        state = Order.objects.filter(id=self.order.id).first().state
        product = OrderItem.objects.select_related('product_info').filter(order_id=self.order.id).first()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['Status'], True)
        self.assertEqual(state, 'sent')
        self.assertEqual(product.product_info.quantity, 0)

    def test_change_to_delivered(self):
        self.change_to_sent()
        response = self.client.patch(reverse('backend:storage'), {'id': self.order.id})
        # print(response.json())
        order = Order.objects.filter(user=self.user.id).first()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['Status'], True)
        self.assertEqual(order.state, 'delivered')

    def test_delete_from_sent(self):
        self.change_to_sent()
        response = self.client.delete(reverse('backend:storage'), {'id': self.order.id})
        # print(response.json())
        order = Order.objects.filter(user=self.user.id).first()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['Status'], False)
        self.assertEqual(response.json()['Errors'], 'Данный заказ нельзя отменить')

    def test_delete_from_confirmed(self):
        self.change_to_confirmed()
        response = self.client.delete(reverse('backend:storage'), {'id': self.order.id})
        order = Order.objects.filter(user=self.user.id, id=self.order.id).first()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['Status'], True)
        self.assertEqual(order.state, 'canceled')

    def test_confirm_with_big_quantity(self):
        self.get_fault_orders()
        response = self.client.put(reverse('backend:order'), {'id': self.order.id})
        # print(response.json())
        order = Order.objects.filter(user=self.user.id).first()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['Status'], False)
        self.assertEqual(order.state, 'new')
