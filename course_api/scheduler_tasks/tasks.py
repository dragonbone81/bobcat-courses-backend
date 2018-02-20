from apscheduler.schedulers.background import BackgroundScheduler
from course_api.data_managers.course_push import UCMercedCoursePush
from django_apscheduler.jobstores import DjangoJobStore

scheduler = BackgroundScheduler()
scheduler.add_jobstore(DjangoJobStore(), 'djangojobstore')


@scheduler.scheduled_job('interval', hours=6, id="course_update")  # to not annoy or whatever
def timed_job():
    # Todo prob move this to data_managers and figure this out
    UCMercedCoursePush().push_courses()()
    print('Course Pull Ran')


scheduler.start()
