from django.shortcuts import render
from django.http import JsonResponse
from rest_framework import viewsets
from course_api.serializers import CourseSerializer

from course_api.data_managers.course_push import UCMercedCoursePush
from course_api.models import Course


# Create your views here.
def course_view(request):
    if request.GET and request.GET.get('pull'):
        UCMercedCoursePush().push_courses()
    return JsonResponse({'success': True})


class CourseViewSet(viewsets.ModelViewSet):
    queryset = Course.objects.all()
    serializer_class = CourseSerializer


class Scheduler(object):
    import os

    from django.core.wsgi import get_wsgi_application

    os.environ['DJANGO_SETTINGS_MODULE'] = 'course_planner.settings'
    application = get_wsgi_application()
    from apscheduler.schedulers.background import BackgroundScheduler
    sched = BackgroundScheduler()

    @sched.scheduled_job('interval', hours=6)  # to not annoy or whatever
    def timed_job():
        UCMercedCoursePush().push_courses()
        print('Course Pull Failed')

    sched.start()
