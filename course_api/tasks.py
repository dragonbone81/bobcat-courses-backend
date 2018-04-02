from __future__ import absolute_import, unicode_literals
from celery import shared_task
from course_api.data_managers.course_push import SubjectClassUpdate


@shared_task
def add(x, y):
    print(x + y)
    return x + y


@shared_task
def mul(x, y):
    return x * y


@shared_task
def xsum(numbers):
    return sum(numbers)


@shared_task
def push():
    SubjectClassUpdate().update_lectures()
