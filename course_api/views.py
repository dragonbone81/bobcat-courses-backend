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
            course['units'] = int(course['units'])
            course['capacity'] = int(course['capacity'])
            course['enrolled'] = int(course['enrolled'])
            if course['available'] == 'Closed':
                course['available'] = 0
            else:
                course['available'] = int(course['available'])
            Course.objects.update_or_create(crn=crn, defaults=course)
    return JsonResponse({'success': True})
