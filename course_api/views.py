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
