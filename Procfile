web: python manage.py runserver 0.0.0.0:$PORT
clock: python course_api/tasks.py
worker: celery -A course_planner worker -l info --without-heartbeat