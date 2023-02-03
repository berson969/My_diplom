#!/bin/sh

celery -A netology_pd_diplom worker info
 # -c 3 --uid=nobody --gid=nogroup