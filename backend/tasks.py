import requests
from yaml import load as load_yaml, Loader

from django.conf import settings
from django.db import IntegrityError
from django.core.mail import EmailMultiAlternatives

from netology_pd_diplom.celery import app
from backend.models import Shop, Category, ProductInfo, Product, Parameter, ProductParameter


@app.task()
def send_order(email, message, **kwargs):
    """
    Отправление письмо при изменении статуса заказа
    """
    try:
        msg = EmailMultiAlternatives(
            # title:
            f"Обновление статуса заказа",
            # message:
            message,
            # from:
            settings.EMAIL_HOST_USER,
            # to:
            [email]
        )
        msg.send()
        return f'Title: {msg.subject}, Message:{msg.body}'
    except Exception:
        raise Exception


@app.task()
def get_price(job_params):  # url, user_id
    stream = requests.get(job_params['url']).content
    data = load_yaml(stream, Loader=Loader)
    try:
        shop, _ = Shop.objects.get_or_create(name=data['shop'],
                                             user_id=job_params['user_id'],
                                             url=job_params['url']
                                             )
    except IntegrityError as e:
        return {'Status': False, 'Error': str(e)}
    for category in data['categories']:
        category_object, _ = Category.objects.get_or_create(id=category['id'], name=category['name'])
        category_object.shops.add(shop.id)
        category_object.save()

    ProductInfo.objects.filter(shop_id=shop.id).delete()
    for item in data['goods']:
        product, _ = Product.objects.get_or_create(name=item['name'], category_id=item['category'])

        product_info = ProductInfo.objects.create(product_id=product.id,
                                                  external_id=item['id'],
                                                  model=item['model'],
                                                  price=item['price'],
                                                  price_rrc=item['price_rrc'],
                                                  quantity=item['quantity'],
                                                  shop_id=shop.id)
        for name, value in item['parameters'].items():
            parameter_object, _ = Parameter.objects.get_or_create(name=name)
            ProductParameter.objects.create(product_info_id=product_info.id,
                                            parameter_id=parameter_object.id,
                                            value=value)
    return {'Status': True}
