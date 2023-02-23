#!/bin/sh

# clean database
#python manage.py flush --no-input

coverage run --source=. --omit=*/migrations/* manage.py test
coverage report