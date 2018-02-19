from apscheduler.schedulers.blocking import BlockingScheduler
from course_api.data_managers.course_pull import UCMercedClassParser
from course_api.models import Course

sched = BlockingScheduler()


@sched.scheduled_job('interval', minutes=1)
def timed_job():
    # Todo prob move this to data_managers
    data = UCMercedClassParser('201810').parse()
    for course in data:
        course_data = course
        course_data.pop('crn')
        Course.objects.update_or_create(crn=course.get('crn'), defaults=course_data)
    print('Course Pull Ran')


sched.start()
