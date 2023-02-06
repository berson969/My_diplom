#!/bin/sh

python manage.py flush --no-input
python manage.py makemigrations
python manage.py migrate
python manage.py collectstatic --no-input --clear

python manage.py createsuperuser --email=admin@admin.com --noinput

gunicorn netology_pd_diplom.wsgi:application --bind 0.0.0.0:8001

# for debug
#python manage.py runserver 0.0.0.0:8001