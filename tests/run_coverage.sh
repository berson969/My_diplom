#!/bin/sh

python manage.py flush --no-input
#celery -A app_celery worker -c 3 --uid=nobody --gid=nogroup --loglevel=INFO
coverage run --source=. --omit=*/migrations/* manage.py test
coverage report