import random

from django.contrib.auth.hashers import check_password
from django_rest_passwordreset.models import ResetPasswordToken
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase, APIClient
from django.urls import reverse

from backend.models import User, ConfirmEmailToken, Contact
from tests.config import FIRST_NAME, LAST_NAME, SUR_NAME, EMAIL_USER, PASSWORD_USER1,\
    PASSWORD_USER2, COMPANY, POSITION, CITY, STREET, HOUSE, STRUCTURE, BUILDING, APARTMENT, PHONE


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

    def create_user(self):
        self.client.post(reverse('backend:user-register'), self.data)

    def confirm_email(self):
        self.create_user()
        token = ConfirmEmailToken.objects.get(user__email=self.data['email'])
        # print(token)
        token.user.is_active = True
        token.user.save()

    def login_user(self):
        self.confirm_email()
        self.client.post(reverse('backend:user-login'), {'email': self.data['email'],
                                                         'password': self.data['password1']})
        token = Token.objects.get(user__email=self.data['email'])
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)
        # user = User.objects.get(email=self.data['email'])

    def add_contacts(self, count=1):
        self.login_user()
        for _ in range(count):
            self.contact['phone'] = random.randint(10000000, 99999999)
            self.client.post(reverse('backend:user-contact'), data=self.contact)

    def reset_password(self):
        self.confirm_email()
        data = dict(email=self.data['email'])
        self.client.post(reverse('backend:password-reset'), data=data)

    def change_type_to_shop(self):
        self.login_user()
        self.data['type'] = 'shop'
        self.client.post(reverse('backend:user-details'), data=self.data)

    def test_create_new_user(self):
        response = self.client.post(reverse('backend:user-register'), self.data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['Status'], True)

    def test_different_password(self):
        self.data['password2'] = 'different'
        response = self.client.post(reverse('backend:user-register'), self.data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['Status'], False)
        self.assertEqual(response.json()['Errors'], 'Пароли не совпадают')

    def test_create_already_exists_user(self):
        self.create_user()
        response = self.client.post(reverse('backend:user-register'), self.data)
        # print(response.json())
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['Status'], False)
        self.assertEqual(response.json()['Errors']['email'],
                                                   ['Пользователь with this email address already exists.'])

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
        self.create_user()
        token = ConfirmEmailToken.objects.get(user__email=self.data['email']).key
        response = self.client.post(reverse('backend:user-register-confirm'),
                                    {'email': self.data['email'], 'token': token})
        # print(response.json())
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['Status'], True)

    def test_confirm_email_without_token(self):
        self.create_user()
        response = self.client.post(reverse('backend:user-register-confirm'),
                                    {'email': self.data['email']})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['Status'], False)
        self.assertEqual(response.json()['Errors'], 'Не указаны все необходимые аргументы')

    def test_get_user_by_email(self):
        self.login_user()
        response = self.client.get(reverse('backend:user-details'), data=self.data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['email'], self.data['email'])

    def test_login_user(self):
        self.confirm_email()
        response = self.client.post(reverse('backend:user-login'),
                                    {'email': self.data['email'], 'password': self.data['password1']})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['Status'], True)
        self.assertIsInstance(response.json()['Token'], str)

    def test_wrong_login_user(self):
        self.confirm_email()
        response = self.client.post(reverse('backend:user-login'),
                                    {'email': self.data['email'], 'password': 'password'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['Status'], False)
        self.assertEqual(response.json()['Errors'], 'Не удалось авторизовать')

    def test_edit_user(self):
        self.login_user()
        self.data['last_name'] = 'new'
        self.data['type'] = 'shop'
        response = self.client.post(reverse('backend:user-details'), data=self.data)
        update_user = User.objects.get(email=self.data['email'])
        self.assertEqual(response.status_code, 200)
        self.assertEqual(update_user.last_name, 'new')
        self.assertEqual(update_user.surname, SUR_NAME)
        self.assertEqual(update_user.type, 'shop')

    def test_edit_user_without_login(self):
        self.login_user()
        self.client.credentials(HTTP_AUTHORIZATION='Token')
        response = self.client.post(reverse('backend:user-details'), {'last_name': 'new'})
        user = User.objects.get(email=self.data['email'])
        # print(response.json())
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()['detail'], 'Invalid token header. No credentials provided.')

    def test_add_contact(self):
        self.login_user()
        response = self.client.post(reverse('backend:user-contact'), data=self.contact)
        contact = Contact.objects.filter(user__email=self.data['email']).first()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['Status'], True)

    def test_add_contact_without_full_data(self):
        self.login_user()
        new_contact = {
                'phone': self.contact['phone'],
                'street': self.contact['street'],
                'building': self.contact['building'],
        }
        response = self.client.post(reverse('backend:user-contact'), data=new_contact)
        # print('response', response.json())
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['Status'], False)
        self.assertEqual(response.json()['Errors'], 'Не указаны все необходимые аргументы')

    def test_add_contact_without_login(self):
        self.confirm_email()
        response = self.client.post(reverse('backend:user-contact'), data=self.contact)
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json()['Status'], False)
        self.assertEqual(response.json()['Error'], 'Log in required')

    def test_edit_contact(self):
        self.add_contacts()
        self.contact['phone'] = '890322123'
        self.contact['id'] = str(Contact.objects.get(user__email=self.data['email']).id)
        response = self.client.put(reverse('backend:user-contact'), data=self.contact)
        # print('response', response.json())
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['Status'], True)

    def test_edit_contact_with_long_phone(self):
        self.add_contacts()
        self.contact['phone'] = PHONE + 'new'
        self.contact['id'] = str(Contact.objects.get(user__email=self.data['email']).id)
        response = self.client.put(reverse('backend:user-contact'), data=self.contact)
        # print('response', response.json())
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['Status'], False)
        self.assertEqual(response.json()['Errors']['phone'],
                         ['Ensure this field has no more than 20 characters.'])

    def test_delete_contact(self):
        self.add_contacts(10)
        data = dict(items='3,4,5')
        response = self.client.delete(reverse('backend:user-contact'),
                                      data=data,
                                      )
        # print('response', response.json())
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['Status'], True)
        self.assertEqual(response.json()['Удалено объектов'], 3)

    def test_delete_not_exists_contact(self):
        self.add_contacts(5)
        data = dict(items='6,7')
        response = self.client.delete(reverse('backend:user-contact'),
                                      data=data,
                                      )
        # print('response', response.json())
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['Status'], True)
        self.assertEqual(response.json()['Удалено объектов'], 0)

    def test_reset_password(self):
        self.confirm_email()
        data = dict(email=self.data['email'])
        response = self.client.post(reverse('backend:password-reset'), data=data)
        token = ResetPasswordToken.objects.get(user__email=self.data['email']).key
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['status'], 'OK')
        self.assertIsInstance(token, str)

    def test_confirm_reset_password(self):
        self.reset_password()
        token = ResetPasswordToken.objects.get(user__email=self.data['email']).key
        data = dict(
            email=self.data['email'],
            password1='new_password',
            password2='new_password',
            token=token,
        )
        response = self.client.post(reverse('backend:password-reset-confirm'), data=data)
        new_password = User.objects.get(email=self.data['email']).password
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['status'], 'OK')
        self.assertIsNotNone(check_password('new_password', new_password))

    def test_reset_password_but_passwords_not_match(self):
        self.reset_password()
        token = ResetPasswordToken.objects.get(user__email=self.data['email']).key
        data = dict(
            email=self.data['email'],
            password1='new_password',
            password2='new_password1',
            token=token,
        )
        response = self.client.post(reverse('backend:password-reset-confirm'), data=data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['Status'], False)
        self.assertEqual(response.json()['Errors'], 'Пароли не совпадают')

