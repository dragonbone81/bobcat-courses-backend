from django.http import JsonResponse
from rest_framework import viewsets
from course_api.serializers import CourseSerializer

from course_api.data_managers.course_push import UCMercedCoursePush
from course_api.models import Course
from django.contrib.auth.models import User
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from rest_framework.views import APIView


class CourseListView(APIView):
    # TODO figure out authentication and permission
    """
    View to receive a class (GLOBAL) and return all associated possibilities.

    * Requires token authentication.
    """

    # authentication_classes = (authentication.TokenAuthentication,)
    permission_classes = ()

    # serializer_class = CourseSerializer

    # Rather than return everything return valid course schedules
    def post(self, request, format=None):
        """
        Return a list of all users.
        """
        courses_to_search = request.data.get('course_list', [])
        courses = dict()
        for course in courses_to_search:
            courses[course] = [CourseSerializer(course).data for course in
                               Course.objects.filter(course_id__istartswith=course)]
        return Response(courses)


# Create your views here.
def course_view(request):
    if request.GET and request.GET.get('pull'):
        UCMercedCoursePush().push_courses()
    return JsonResponse({'success': True})


class CourseViewSet(viewsets.ModelViewSet):
    queryset = Course.objects.all().order_by('crn')
    serializer_class = CourseSerializer
    filter_fields = '__all__'
    search_fields = '__all__'
