import os
import django

# set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'course_planner.settings')
django.setup()
from apscheduler.schedulers.background import BackgroundScheduler
from course_api.data_managers.course_push import UCMercedCoursePush

scheduler = BackgroundScheduler()


@scheduler.scheduled_job('interval', hours=6, id="course_update")  # to not annoy or whatever
def timed_job():
    # Todo prob move this to data_managers and figure this out
    UCMercedCoursePush().push_courses()
    print('Course Pull Ran')


scheduler.start()
