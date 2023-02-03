from app_celery import app
from django.conf import settings
from django.core.mail import EmailMultiAlternatives

from backend.models import User


@app.task
# @receiver(send_order)
def send_order(user_id, message, **kwargs):
    """
    Отправление письмо при изменении статуса заказа
    """
    try:
        # send an e-mail to the user
        user = User.objects.get(id=user_id)

        msg = EmailMultiAlternatives(
            # title:
            f"Обновление статуса заказа",
            # message:
            message,
            # from:
            settings.EMAIL_HOST_USER,
            # to:
            [user.email]
        )
        msg.send()
        return f'Title: {msg.subject}, Message:{msg.body}'
    except Exception:
        raise Exception
