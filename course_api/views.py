from django.http import JsonResponse
from django.db.models import Q
from django.contrib.auth.models import User
from rest_framework import viewsets
from course_api.serializers import CourseSerializer

from course_api.data_managers.course_push import UCMercedCoursePush
from course_api.models import Course
from rest_framework.renderers import JSONRenderer, BrowsableAPIRenderer
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.tokens import RefreshToken


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


class UserInfo(APIView):
    authentication_classes = (JWTAuthentication,)
    permission_classes = (IsAuthenticated,)
    renderer_classes = (JSONRenderer, BrowsableAPIRenderer)

    def get(self, request):
        user = {'username': request.user.username, 'email': request.user.email, 'name': request.user.get_full_name(),
                'first_name': request.user.first_name, 'last_name': request.user.last_name}
        return Response(user)


class UserRegistration(APIView):
    permission_classes = ()
    renderer_classes = (JSONRenderer, BrowsableAPIRenderer)

    def post(self, request):
        first_name = request.data.get('first_name')
        last_name = request.data.get('last_name')
        user = {'username': request.data.get('username'), 'password': request.data.get('password'),
                'first_name': first_name, 'last_name': last_name, 'email': request.data.get('email')}
        if not User.objects.filter(username=request.data.get('username')):
            user = User.objects.create_user(**user)
            token_jwt = RefreshToken.for_user(user)
            response = {
                'user': {
                    'username': request.data.get('username'),
                    'name': user.get_full_name(), 'first_name': user.first_name, 'last_name': user.last_name,
                    'email': request.data.get('email')
                },
                'api_keys': {
                    'access': str(token_jwt.access_token),
                    'refresh': str(token_jwt)
                },
            }
            return Response(response)
        else:
            return Response({'error': 'User Already Exists'}, status=status.HTTP_406_NOT_ACCEPTABLE)


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


class CoursesSearch(APIView):
    # TODO figure out authentication and permission
    """
    """

    # authentication_classes = (JWTAuthentication,)
    permission_classes = ()

    # serializer_class = CourseSerializer
    renderer_classes = (JSONRenderer, BrowsableAPIRenderer)

    # Rather than return everything return valid course schedules
    def get(self, request):
        course = request.GET.get('course', None)
        course_subj = course[0:3]
        course_number = course[3:6]
        courses = Course.objects.filter(
            Q(course_id__istartswith=course_subj) & Q(course_id__iregex=r"[^A-Za-zs.]$") & Q(
                course_id__icontains=course_number))

        courses = [CourseSerializer(course).data for course in courses]
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
