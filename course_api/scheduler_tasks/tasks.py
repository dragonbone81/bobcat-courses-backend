from apscheduler.schedulers.blocking import BlockingScheduler
from course_api.data_managers.course_pull import UCMercedClassParser

sched = BlockingScheduler()


@sched.scheduled_job('interval', minutes=1)
def timed_job():
    UCMercedClassParser('201810').parse()
    print('Course Pull Ran')


sched.start()
