from __future__ import absolute_import, unicode_literals
from celery import shared_task
from course_api.data_managers.course_push import SubjectClassUpdate, UCMercedCoursePush


@shared_task
def course_push_task():
    SubjectClassUpdate().update_lectures()
    UCMercedCoursePush().push_courses()
    print('course_push ran')
