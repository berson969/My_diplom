#!/bin/sh

celery -A netology_pd_diplom worker -l INFO --uid=0 -E
