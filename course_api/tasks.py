from celery import shared_task
# from course_api.data_managers.course_push import UCMercedCoursePush, SubjectClassUpdate


@shared_task
def name_of_your_function():
    print('celery_task')
    # print("starting course_push")
    # UCMercedCoursePush().push_courses()
    # print("finished first push")
    # SubjectClassUpdate().update_lectures()
    # print("finished full push")
