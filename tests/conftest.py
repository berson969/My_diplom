from random import randint

from rest_framework.authtoken.models import Token
from django.urls import reverse

from backend.models import User, ConfirmEmailToken, ProductInfo, Contact, Order
from tests.config_test import URL, FIRST_NAME, LAST_NAME, SUR_NAME, EMAIL_USER, PASSWORD_USER1, \
    PASSWORD_USER2, COMPANY, POSITION, CITY, STREET, HOUSE, STRUCTURE, BUILDING, APARTMENT, PHONE

CONTACT = {
    'city': CITY,
    'street': STREET,
    'house': HOUSE,
    'structure': STRUCTURE,
    'building': BUILDING,
    'apartment': APARTMENT,
    'phone': PHONE,
}
DATA = {
    'first_name': FIRST_NAME,
    'last_name': LAST_NAME,
    'surname': SUR_NAME,
    'email': EMAIL_USER,
    'password1': PASSWORD_USER1,
    'password2': PASSWORD_USER2,
    'company': COMPANY,
    'position': POSITION,
}


def create_user(client, type):
    DATA['email'] = f"user_{randint(10000, 99999)}@admin.ru"
    DATA['type'] = type
    client.post(reverse('backend:user-register'), DATA)
    user = User.objects.get(email=DATA['email'])
    return user


def confirm_email(client):
    user = create_user(client, 'shop')
    token = ConfirmEmailToken.objects.get(user_id=user.id)
    client.post(reverse('backend:user-register-confirm'), {'email': user.email,
                                                           'token': token.key})
    return user


def login_user(client):
    user = confirm_email(client)
    client.post(reverse('backend:user-login'), {'email': user.email, 'password': PASSWORD_USER1})
    token = Token.objects.get(user__id=user.id)
    client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)
    return client, user


def add_contacts(client, count=1):
    for _ in range(count):
        CONTACT['phone'] = randint(10000000, 99999999)
        client.post(reverse('backend:user-contact'), data=CONTACT)
    return Contact.objects.first()


def reset_password(client):
    user = confirm_email(client)
    data = dict(email=user.email)
    client.post(reverse('backend:password-reset'), data=data)
    return User.objects.get(id=user.id)


def create_shop(client):
    client, user = login_user(client)
    client.post(reverse('backend:partner-update'), data={'url': URL})
    return ProductInfo.objects.select_related('shop').filter(shop_id__user_id=user.id).first(), user


def add_orders(client):
    product, user = create_shop(client)
    data = dict(items=f'[{{"product_info": {product.id}, "quantity": 2}},'
                      f' {{"product_info": {product.id + 1}, "quantity": 3}}]'
                )
    client_buyer, user_buyer = login_user(client)
    client_buyer.post(reverse('backend:basket'), data=data)
    return client_buyer, user_buyer


def get_orders(client):
    client, user = add_orders(client)
    contact = add_contacts(client)
    order = Order.objects.filter(user=user.id).first()
    client.post(reverse('backend:order'), {'id': order.id, 'contact': contact.id})
    return order, user


def change_to_confirmed(client):
    order, user = get_orders(client)
    client.put(reverse('backend:order'), {'id': order.id})
    return order, user


def change_to_assembled(client):
    order, user = change_to_confirmed(client)
    client.post(reverse('backend:storage'), {'id': order.id})
    return order, user


def change_to_sent(client):
    order, user = change_to_assembled(client)
    client.patch(reverse('backend:storage'), {'id': order.id})
    return order, user


def get_fault_orders(client):
    product, user = create_shop(client)
    data = dict(items=f'[{{"product_info": {product.id}, "quantity": 100}},'
                      f' {{"product_info": {product.id + 1}, "quantity": 1}}]'
                )
    client, user = login_user(client)
    client.post(reverse('backend:basket'), data=data)
    order = Order.objects.filter(user=user.id).first()
    client.post(
        reverse('backend:order'),
        {
            'id': order.id,
            'contact': add_contacts(client).id
        }
    )
    return order, user
