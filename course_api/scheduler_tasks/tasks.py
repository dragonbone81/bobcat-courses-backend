from course_api.tasks import course_push_task


def timed_job():
    course_push_task.delay()


timed_job()
