#!/bin/sh

python manage.py flush --no-input
python manage.py makemigrations
python manage.py migrate
python manage.py collectstatic --no-input --clear
#python manage.py runserver 0.0.0.0:8000
#celery -A backend.celery_signals.app_celery worker -c 3 --uid=nobody --gid=nogroup
gunicorn netology_pd_diplom.wsgi:application --bind 0.0.0.0:8001