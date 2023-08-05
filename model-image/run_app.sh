#!/bin/bash/

celery -A app worker.make_celery --loglevel=INFO -P eventlet
flask --app app run