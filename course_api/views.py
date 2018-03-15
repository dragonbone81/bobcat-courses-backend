from django.http import JsonResponse
from django.db.models import Q
from django.contrib.auth.models import User
from rest_framework import viewsets
from course_api.serializers import CourseSerializer
import re
from course_api.utils.simplified_course_name import get_simple
from course_api.data_managers.course_scheduler import CourseScheduler

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
    authentication_classes = (JWTAuthentication, SessionAuthentication, BasicAuthentication)
    permission_classes = (IsAuthenticated,)
    renderer_classes = (JSONRenderer, BrowsableAPIRenderer)

    def retrieve(self, request, pk=None):
        return Response(None)

    def list(self, request, format=None):
        # TODO if someone searches computer science it does not return...
        course = request.GET.get('course', None)
        term = request.GET.get('term', None)
        if not course or not term:
            return Response(None)
        course_subj = "".join(re.findall("[a-zA-Z]+", course))
        course_number = "".join(re.findall("[0-9]+", course))
        courses = Course.objects.filter((Q(course_id__iregex=r"[^A-Za-zs.]$") & (
                Q(subject__icontains=course_subj) | Q(course_id__icontains=course_subj)) & Q(
            course_id__icontains=course_number)) & Q(term=term))
        courses_data = {}
        for course in courses:
            try:
                subject = SubjectCourse.objects.get(course_name=get_simple(course.course_id), term=term)
            except SubjectCourse.DoesNotExist:
                continue
            courses_data[subject.course_name] = subject.course_name
        return Response([course for key, course in courses_data.items()] or [])


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

    post: Returns valid schedules for classes - {"course_list": ["CSE-120", "CSE-150"], "term":"201810"}
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
        if not term:
            return Response({"Error": "No Term"})
        generator = CourseScheduler(term)
        courses = generator.get_valid_schedules(courses_to_search)

        return Response(courses[:65])

