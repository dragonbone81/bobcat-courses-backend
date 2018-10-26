web: gunicorn course_planner.wsgi
clock: python course_api/tasks.py
worker: celery -A course_planner worker -l info --without-heartbeat
