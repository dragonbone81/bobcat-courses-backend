from django.http import JsonResponse
from rest_framework import viewsets
from course_api.serializers import CourseSerializer

from course_api.data_managers.course_push import UCMercedCoursePush
from course_api.models import Course
from rest_framework.renderers import JSONRenderer, BrowsableAPIRenderer
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication


# TODO schedule view

class ExampleJWT(APIView):
    """
    * Requires JWT authentication.
    Example token authentication
    Get token from (username/password): api/auth/token/obtain
    Pass here or any view as Authentication: Bearer <token>
    Enjoy :)
    """

    authentication_classes = (JWTAuthentication,)
    permission_classes = (IsAuthenticated,)
    renderer_classes = (JSONRenderer, BrowsableAPIRenderer)

    def get(self, request):
        user = {'username': request.user.username, 'email': request.user.email, 'name': request.user.get_full_name()}
        return Response(user)


class CourseListView(APIView):
    # TODO figure out authentication and permission
    """
    View to receive a class (GLOBAL) and return all associated possibilities.
    * Sample python request -- requests.post(url="http://127.0.0.1:8000/api/courses/course-match", json={"course_list": ["CSE-120", "CSE-150"]}, params={'format': 'json'}).json()
    * Requires token authentication.
    """

    # authentication_classes = (JWTAuthentication,)
    permission_classes = ()

    # serializer_class = CourseSerializer
    renderer_classes = (JSONRenderer, BrowsableAPIRenderer)

    # Rather than return everything return valid course schedules
    def post(self, request):
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
