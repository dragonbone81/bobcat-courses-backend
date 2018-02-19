from django.shortcuts import render
from django.http import JsonResponse

from course_api.data_managers.course_pull import UCMercedClassParser
from course_api.models import Course


# Create your views here.
def course_view(request):
    if request.GET and request.GET.get('pull'):
        data = UCMercedClassParser('201810').parse()
        for course in data:
            # TODO weird thing with python and not references
            crn = course.get('crn')
            course.pop('crn')
            Course.objects.update_or_create(crn=crn, defaults=course)
    return JsonResponse({'success': True})
