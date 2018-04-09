web: gunicorn course_planner.wsgi -k gevent --worker-connections $WORKER_CONNECTIONS --bind 0.0.0.0:$PORT --config gunicorn_config.py --max-requests 10000 --max-requests-jitter 1000
clock: python course_api/tasks.py
worker: celery -A course_planner worker -l info --without-heartbeat