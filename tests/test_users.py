from django.contrib.auth.hashers import check_password
from django_rest_passwordreset.models import ResetPasswordToken
from rest_framework.test import APITestCase, APIClient
from django.urls import reverse

from backend.models import User, ConfirmEmailToken
from tests.config_test import FIRST_NAME, LAST_NAME, SUR_NAME, EMAIL_USER, PASSWORD_USER1, \
    PASSWORD_USER2, COMPANY, POSITION, CITY, STREET, HOUSE, STRUCTURE, BUILDING, APARTMENT, PHONE
from tests.conftest import create_user, confirm_email, login_user, add_contacts, reset_password


class UserTests(APITestCase):

    def setUp(self) -> None:
        self.client = APIClient()
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
            'house': HOUSE,
            'structure': STRUCTURE,
            'building': BUILDING,
            'apartment': APARTMENT,
            'phone': PHONE,
        }

    def test_create_new_user(self):
        response = self.client.post(reverse('backend:user-register'), self.data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['Status'], True)

    def test_different_password(self):
        self.data['password2'] = 'different'
        response = self.client.post(reverse('backend:user-register'), self.data)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()['Status'], False)
        self.assertEqual(response.json()['Errors'], 'Пароли не совпадают')

    def test_create_already_exists_user(self):
        user = create_user(self.client, 'shop')
        self.data['email'] = user.email
        response = self.client.post(reverse('backend:user-register'), self.data)
        # print(response.json())
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['Status'], False)
        self.assertEqual(response.json()['Errors']['email'], ['Пользователь with this email address already exists.'])

    def test_create_user_easy_password(self):
        self.data['password1'] = '1a'
        self.data['password2'] = '1a'
        response = self.client.post(reverse('backend:user-register'), self.data)
        # print(response.json())
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['Status'], False)
        self.assertEqual(response.json()['Errors']['password'],
                         ['This password is too short. It must contain at least 8 characters.'])

    def test_confirm_email(self):
        user = create_user(self.client, 'shop')
        token = ConfirmEmailToken.objects.get(user_id=user.id)
        response = self.client.post(reverse('backend:user-register-confirm'),
                                    {'email': user.email, 'token': token.key})
        # print(response.json())
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['Status'], True)

    def test_confirm_email_without_token(self):
        user = create_user(self.client, 'shop')
        response = self.client.post(reverse('backend:user-register-confirm'),
                                    {'email': user.email})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['Status'], False)
        self.assertEqual(response.json()['Errors'], 'Не указаны все необходимые аргументы')

    def test_get_user_by_email(self):
        self.client, user = login_user(self.client)
        response = self.client.get(reverse('backend:user-details'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['email'], user.email)

    def test_login_user(self):
        user = confirm_email(self.client)
        response = self.client.post(reverse('backend:user-login'),
                                    {'email': user.email, 'password': PASSWORD_USER1})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['Status'], True)
        self.assertIsInstance(response.json()['Token'], str)

    def test_wrong_login_user(self):
        user = confirm_email(self.client)
        response = self.client.post(reverse('backend:user-login'),
                                    {'email': user.email, 'password': 'password'})
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json()['Status'], False)
        self.assertEqual(response.json()['Errors'], 'Не удалось авторизовать')

    def test_edit_user(self):
        self.client, user = login_user(self.client)
        self.data['last_name'] = 'new'
        self.data['type'] = 'shop'
        response = self.client.post(reverse('backend:user-details'), data=self.data)
        # print(response.json())
        update_user = User.objects.get(id=user.id)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(update_user.last_name, 'new')
        self.assertEqual(update_user.type, 'shop')

    def test_edit_user_wrong_change_password(self):
        self.client, user = login_user(self.client)
        self.data['last_name'] = 'new'
        self.data['password1'] = 'qscefbrd34fg'
        self.data['password2'] = 'adlvdjojfvvmf'
        response = self.client.post(reverse('backend:user-details'), data=self.data)
        # print(response.json())
        update_user = User.objects.get(id=user.id)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(update_user.last_name, 'last')
        self.assertEqual(response.json()['Status'], False)
        self.assertEqual(response.json()['Errors'], 'Пароли не совпадают')

    def test_edit_user_without_login(self):
        self.client, user = login_user(self.client)
        self.client.credentials(HTTP_AUTHORIZATION='Token')
        response = self.client.post(reverse('backend:user-details'), {'last_name': 'new'})
        # print(response.json())
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()['detail'], 'Invalid token header. No credentials provided.')

    def test_add_contact(self):
        self.client, user = login_user(self.client)
        response = self.client.post(reverse('backend:user-contact'), data=self.contact)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['Status'], True)

    def test_add_contact_without_full_data(self):
        self.client, user = login_user(self.client)
        new_contact = {
            'phone': self.contact['phone'],
            'street': self.contact['street'],
            'building': self.contact['building'],
        }
        response = self.client.post(reverse('backend:user-contact'), data=new_contact)
        # print('response', response.json())
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()['Status'], False)
        self.assertEqual(response.json()['Errors'], 'Не указаны все необходимые аргументы')

    def test_add_contact_without_login(self):
        confirm_email(self.client)
        response = self.client.post(reverse('backend:user-contact'), data=self.contact)
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json()['Status'], False)
        self.assertEqual(response.json()['Error'], 'Log in required')

    def test_edit_contact(self):
        client, user = login_user(self.client)
        contact = add_contacts(client)
        update_data = {'phone': '890322123', 'id': contact.id}
        response = client.put(reverse('backend:user-contact'), data=update_data)
        # print('response', response.json())
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['Status'], True)

    def test_edit_contact_with_long_phone(self):
        client, user = login_user(self.client)
        contact = add_contacts(client)
        update_data = {'phone': PHONE + 'new-long-number', 'id': contact.id}
        response = client.put(reverse('backend:user-contact'), data=update_data)
        # print('response', response.json())
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['Status'], False)
        self.assertEqual(response.json()['Errors']['phone'],
                         ['Ensure this field has no more than 20 characters.'])

    def test_delete_contact(self):
        client, user = login_user(self.client)
        contact = add_contacts(client, 10)
        data = dict(items=f'{contact.id},{contact.id + 1},{contact.id + 2}')
        response = client.delete(reverse('backend:user-contact'), data=data)
        # print('response', response.json())
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['Status'], True)
        self.assertEqual(response.json()['Удалено объектов'], 3)

    def test_get_contacts(self):
        client, user = login_user(self.client)
        add_contacts(client, 5)
        response = client.get(reverse('backend:user-contact'))
        # print('response', response.json())
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.json(), list)
        self.assertEqual(len(response.json()), 5)

    def test_delete_not_exists_contact(self):
        client, user = login_user(self.client)
        add_contacts(client, 5)
        data = dict(items='6,7')
        response = client.delete(reverse('backend:user-contact'), data=data)
        # print('response', response.json())
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['Status'], True)
        self.assertEqual(response.json()['Удалено объектов'], 0)

    def test_reset_password(self):
        user = confirm_email(self.client)
        data = dict(email=user.email)
        response = self.client.post(reverse('backend:password-reset'), data=data)
        token = ResetPasswordToken.objects.get(user__email=user.email).key
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['status'], 'OK')
        self.assertIsInstance(token, str)

    def test_confirm_reset_password(self):
        user = reset_password(self.client)
        token = ResetPasswordToken.objects.get(user__email=user.email).key
        data = dict(
            email=user.email,
            password1='new_password',
            password2='new_password',
            token=token,
        )
        response = self.client.post(reverse('backend:password-reset-confirm'), data=data)
        new_password = User.objects.get(email=user.email).password
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['status'], 'OK')
        self.assertIsNotNone(check_password('new_password', new_password))

    def test_reset_password_but_passwords_not_match(self):
        user = reset_password(self.client)
        token = ResetPasswordToken.objects.get(user__email=user.email).key
        data = dict(
            email=user.email,
            password1='new_password',
            password2='new_password1',
            token=token,
        )
        response = self.client.post(reverse('backend:password-reset-confirm'), data=data)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()['Status'], False)
        self.assertEqual(response.json()['Errors'], 'Пароли не совпадают')
