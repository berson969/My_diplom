import os

from celery import Celery
from django.core.mail import EmailMultiAlternatives

from backend.models import User
# from django.conf import settings
from netology_pd_diplom import settings

# import config

# Set the default Django settings module for the 'celery' program.
# os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'netology_pd_diplom.settings')

app = Celery('netology_pd_diplom',
             broker_url=settings.CELERY_BROKER_URL,
             result_backend=settings.CELERY_BROKER_URL,
             )

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.

# app.conf.update(
#     broker_url=f"redis://{os.getenv('PG_HOST')}:6379/1",
#     result_backend=f"redis://{os.getenv('PG_HOST')}:6379/2",
#     task_serializer='json',
#     accept_content=['json'],  # Ignore other content
#     result_serializer='json',
#     timezone='Europe/Oslo',
#     enable_utc=True,
# )

# app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django apps.
app.autodiscover_tasks()


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f'Request: {self.request!r}')


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
