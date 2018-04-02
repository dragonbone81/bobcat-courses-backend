from apscheduler.schedulers.blocking import BlockingScheduler
from course_api.tasks import course_push_task

scheduler = BlockingScheduler()


@scheduler.scheduled_job('interval', minutes=3)
def timed_job():
    course_push_task.delay()


scheduler.start()
