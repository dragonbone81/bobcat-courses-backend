from django.http import JsonResponse
from django.db.models import Q
from django.contrib.auth.models import User
from rest_framework import viewsets
from course_api.serializers import CourseSerializer
import re
from course_api.utils.simplified_course_name import get_simple
from course_api.data_managers.ScheduleHTML import create_schedules
from course_api.data_managers.course_scheduler import CourseScheduler
from course_api.data_managers.my_registration import CourseRegistration

from course_api.data_managers.course_push import UCMercedCoursePush, SubjectClassUpdate
from course_api.models import Course, SubjectCourse
from rest_framework.renderers import JSONRenderer, BrowsableAPIRenderer
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.viewsets import ViewSet
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.authentication import SessionAuthentication, BasicAuthentication

from rest_framework_simplejwt.tokens import RefreshToken

from django.shortcuts import render


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


class UserInfo(ViewSet):
    """
    Requires Authentication - {Authorization: "Bearer " + access_token}

    get: Return user info of Auth/JWT holder : {username, email, name, firstname, lastname}
    """
    authentication_classes = (JWTAuthentication, SessionAuthentication, BasicAuthentication)
    permission_classes = (IsAuthenticated,)
    renderer_classes = (JSONRenderer, BrowsableAPIRenderer)

    def list(self, request, format=None):
        user = {'username': request.user.username, 'email': request.user.email, 'name': request.user.get_full_name(),
                'first_name': request.user.first_name, 'last_name': request.user.last_name}
        return Response(user)


class UserRegistration(ViewSet):
    """
    Requires Authentication and Staff Status - {Authorization: "Bearer " + access_token}

    post: Return user info and access_tokens when post : {username, email, name, firstname, lastname, password}
    """
    authentication_classes = (JWTAuthentication, SessionAuthentication, BasicAuthentication)
    permission_classes = (IsAdminUser,)
    renderer_classes = (JSONRenderer, BrowsableAPIRenderer)

    def retrieve(self, request, pk=None):
        return Response(None)

    def list(self, request, format=None):
        return Response(None)

    def post(self, request):
        first_name = request.data.get('first_name', "Anonymous")
        last_name = request.data.get('last_name', "Panda")
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


class CourseListView(ViewSet):
    """
    View to receive a class (GLOBAL) and return all associated possibilities.
    * Sample python request -- {"course_list": ["CSE-120", "CSE-150"], "term":"201810"}
    * Requires token authentication.
    """

    authentication_classes = (JWTAuthentication, SessionAuthentication, BasicAuthentication)
    permission_classes = (IsAuthenticated,)
    renderer_classes = (JSONRenderer, BrowsableAPIRenderer)

    def retrieve(self, request, pk=None):
        return Response(None)

    def list(self, request, format=None):
        return Response(None)

    def post(self, request):
        """
        Return a list of all courses.
        """
        courses_to_search = request.data.get('course_list', [])
        term = request.data.get('term')
        if not term:
            return Response({"Error": "No Term"})
        courses = dict()
        for course in courses_to_search:
            if isinstance(course, str):
                courses[course] = [CourseSerializer(course).data for course in
                                   Course.objects.filter(
                                       (Q(course_id__istartswith=course) | Q(simple_name__icontains=course)) & Q(
                                           term=term))]
            if isinstance(course, dict):
                courses[course.get('id')] = [CourseSerializer(course).data for course in
                                             Course.objects.filter(simple_name__icontains=course.get('id'), term=term)]
        return Response(courses)


class CoursesSearch(ViewSet):
    """
    Requires Authentication - {Authorization: "Bearer " + access_token}

    get: ?course=CSE-120&term=201810 or course=CSE&term=201810  -   filtering by course_id, subject or simple name returns list of matching simple_names
    TERM but be there
    """
    # authentication_classes = (JWTAuthentication, SessionAuthentication, BasicAuthentication)
    permission_classes = ()
    renderer_classes = (JSONRenderer, BrowsableAPIRenderer)

    def retrieve(self, request, pk=None):
        return Response(None)

    def list(self, request, format=None):
        # this just matches simple name
        course = request.GET.get('course', None)
        term = request.GET.get('term', None)
        if not course or not term:
            return Response(None)
        course_with_dash = course
        if '-' not in course_with_dash:
            for i, char in enumerate(course_with_dash):
                if char.isdigit():
                    course_with_dash = "{}-{}".format(course_with_dash[0:i], course_with_dash[i:])
                    break
        simple_courses = [course.course_name for course in
                          SubjectCourse.objects.filter(course_name__istartswith=course_with_dash, term=term).order_by(
                              'course_name')]
        return Response(simple_courses)


# Create your views here.
def course_view(request):
    if request.GET and request.GET.get('pull'):
        UCMercedCoursePush().push_courses()
    if request.GET and request.GET.get('simple'):
        SubjectClassUpdate().update_lectures()
    return JsonResponse({'success': True})


class CourseViewSet(viewsets.ModelViewSet):
    queryset = Course.objects.all().order_by('crn')
    serializer_class = CourseSerializer
    filter_fields = '__all__'
    search_fields = '__all__'


class SchedulesListView(ViewSet):
    """
    Requires Authentication - {Authorization: "Bearer " + access_token}

    post: Returns valid schedules for classes - {"course_list": ["CSE-120", "CSE-150"], "term":"201830", "earliest_time":1000, "latest_time":2100, "gaps";"desc||asc", "days";"desc||asc"}
    """
    authentication_classes = (JWTAuthentication, SessionAuthentication, BasicAuthentication)
    permission_classes = (IsAuthenticated,)
    renderer_classes = (JSONRenderer, BrowsableAPIRenderer)

    def retrieve(self, request, pk=None):
        return Response(None)

    def list(self, request, format=None):
        return Response(None)

    def post(self, request):
        """
        Return a list of all courses.
        """
        courses_to_search = request.data.get('course_list', [])
        term = request.data.get('term', None)
        earliest_time = request.data.get('earliest_time', None)
        latest_time = request.data.get('latest_time', None)
        days = request.data.get('days', 'asc')
        gaps = request.data.get('gaps', 'asc')
        if not term:
            return Response({"Error": "No Term"})
        generator = CourseScheduler(term, earliest_time=earliest_time, latest_time=latest_time, days=days, gaps=gaps)
        courses = generator.get_valid_schedules(courses_to_search)

        return Response(courses[:65])


class CasRegistration(ViewSet):
    """
    Requires Authentication - {Authorization: "Bearer " + access_token}

    post: Registers you for classes
    example: {"crns":[123, 1234, 123], "username":"***", "password":"***", "term":201820} for summer term
    """
    authentication_classes = (JWTAuthentication, SessionAuthentication, BasicAuthentication)
    permission_classes = (IsAuthenticated,)
    renderer_classes = (JSONRenderer, BrowsableAPIRenderer)

    def retrieve(self, request, pk=None):
        return Response(None)

    def list(self, request, format=None):
        return Response(None)

    def post(self, request):
        crns = request.data.get('crns')
        username = request.data.get('username')
        password = request.data.get('password')
        term = request.data.get('term')
        response = CourseRegistration(course_crns=crns, term=term,
                                      auth={'username': username, 'password': password}).register()
        return Response(response)


def calendar(request):
    if request.POST:
        schedules, all_schedule_ids, selected_classes = create_schedules(request)
        return render(request, 'calendar.html',
                      {'schedules': schedules,
                       'times': [{'m': '7:00', 'c': '7:00am'}, {'m': '7:30', 'c': '7:30am'},
                                 {'m': '8:00', 'c': '8:00am'},
                                 {'m': '8:30', 'c': '8:30am'}, {'m': '9:00', 'c': '9:00am'},
                                 {'m': '9:30', 'c': '9:30am'},
                                 {'m': '10:00', 'c': '10:00am'}, {'m': '10:30', 'c': '10:30am'},
                                 {'m': '11:00', 'c': '11:00am'}, {'m': '11:30', 'c': '11:30am'},
                                 {'m': '12:00', 'c': '12:00pm'}, {'m': '12:30', 'c': '12:30pm'},
                                 {'m': '13:00', 'c': '1:00pm'}, {'m': '13:30', 'c': '1:30pm'},
                                 {'m': '14:00', 'c': '2:00pm'},
                                 {'m': '14:30', 'c': '2:30pm'},
                                 {'m': '15:00', 'c': '3:00pm'}, {'m': '15:30', 'c': '3:30pm'},
                                 {'m': '16:00', 'c': '4:00pm'}, {'m': '16:30', 'c': '4:30pm'},
                                 {'m': '17:00', 'c': '5:00pm'}, {'m': '17:30', 'c': '5:30pm'},
                                 {'m': '18:00', 'c': '6:00pm'}, {'m': '18:30', 'c': '6:30pm'},
                                 {'m': '19:00', 'c': '7:00pm'},
                                 {'m': '19:30', 'c': '7:30pm'},
                                 {'m': '20:00', 'c': '8:00pm'}, {'m': '20:30', 'c': '8:30pm'},
                                 {'m': '21:00', 'c': '9:00pm'}, {'m': '21:30', 'c': '9:30pm'},
                                 {'m': '22:00', 'c': '10:00pm'}, {'m': '22:30', 'c': '10:30pm'}],
                       'total_schedules': len(schedules), 'all_schedule_ids': all_schedule_ids,
                       'selected_classes': selected_classes})
    course_by_times = {'M': {}, 'T': {}, 'W': {}, 'R': {}, 'F': {}}
    return render(request, 'calendar.html',
                  {'calendar': course_by_times,
                   'times': ['7:00', '7:30', '8:00', '8:30', '9:00', '9:30', '10:00', '10:30', '11:00', '11:30',
                             '12:00', '12:30', '13:00', '13:30', '14:00',
                             '14:30',
                             '15:00', '15:30', '16:00', '16:30', '17:00', '17:30', '18:00', '18:30', '19:00', '19:30',
                             '20:00', '20:30', '21:00']})
