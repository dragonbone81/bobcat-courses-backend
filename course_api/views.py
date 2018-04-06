from django.http import JsonResponse
from django.db.models import Q
from django.contrib.auth.models import User
from rest_framework import viewsets
from course_api.serializers import CourseSerializer, ScheduleSerializer, SubjectCourseSerializer
import re
from course_api.utils.simplified_course_name import get_simple
from course_api.tasks import course_push_task

from django.contrib.auth import authenticate, login
from course_api.data_managers.ScheduleHTML import get_html_courses
from course_api.data_managers.course_scheduler import CourseScheduler
from course_api.data_managers.my_registration import CourseRegistration
from course_api.data_managers.loadSchedules import GetSchedules

from course_api.data_managers.course_push import UCMercedCoursePush, SubjectClassUpdate
from course_api.models import Course, SubjectCourse, Schedule
from rest_framework.renderers import JSONRenderer, BrowsableAPIRenderer
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.viewsets import ViewSet
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.authentication import SessionAuthentication, BasicAuthentication

from rest_framework_simplejwt.tokens import RefreshToken

from django.shortcuts import render, redirect
from course_api.utils.get_schedule_info import getInfoForSchedule


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
    # authentication_classes = (JWTAuthentication, SessionAuthentication, BasicAuthentication)
    permission_classes = ()
    renderer_classes = (JSONRenderer, BrowsableAPIRenderer)

    def retrieve(self, request, pk=None):
        return Response(None)

    def list(self, request, format=None):
        return Response(None)

    def post(self, request):
        import random
        from course_api.data_managers.anonymous_names import names
        first_name = request.data.get('first_name', "Anonymous")
        last_name = request.data.get('last_name', random.choice(names))
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
    """

    # authentication_classes = (JWTAuthentication, SessionAuthentication, BasicAuthentication)
    permission_classes = ()
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
                                   Course.objects.filter(simple_name__iexact=course, term=term)]
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
        simple_courses = [{'name': course.course_name, 'description': course.course_description} for course in
                          SubjectCourse.objects.filter(Q(course_name__icontains=course_with_dash), term=term).order_by(
                              'course_name')]
        if not simple_courses:
            simple_courses = [{'name': course.course_name, 'description': course.course_description} for course in
                              SubjectCourse.objects.filter(course_description__icontains=course, term=term).order_by(
                                  'course_name')]
            temp_list = []
            course_list = course.split()
            for course_filter in simple_courses:
                course_filter_list = course_filter.get('description').split()
                match = False
                for item in course_list:
                    for item_course in course_filter_list:
                        if item_course.startswith(item):
                            match = True
                if match:
                    temp_list.append(course_filter)
            simple_courses = temp_list
        simple_courses.sort(key=lambda x: int(''.join(filter(str.isdigit, x['name'].split('-')[1]))))
        return Response(simple_courses)


class GetTerms(ViewSet):
    """
    returns total available terms
    """
    # authentication_classes = (JWTAuthentication, SessionAuthentication, BasicAuthentication)
    permission_classes = ()
    renderer_classes = (JSONRenderer, BrowsableAPIRenderer)

    def retrieve(self, request, pk=None):
        return Response(None)

    def list(self, request, format=None):
        # this just matches simple name
        simple_courses = SubjectCourse.objects.all()
        terms = list()
        for course in simple_courses:
            if course.term not in terms:
                terms.append(course.term)
        return Response(terms)


# Create your views here.
def course_view(request):
    if request.GET and request.GET.get('pull'):
        UCMercedCoursePush().push_courses()
    elif request.GET and request.GET.get('simple'):
        SubjectClassUpdate().update_lectures()
    else:
        course_push_task.delay()
    return JsonResponse({'success': True})


def ping(request):
    return JsonResponse({'status': 'UP'})


class CourseViewSet(viewsets.ModelViewSet):
    queryset = Course.objects.all().order_by('crn')
    serializer_class = CourseSerializer
    filter_fields = '__all__'
    search_fields = '__all__'


class SubjectCourseViewSet(viewsets.ModelViewSet):
    queryset = SubjectCourse.objects.all().order_by('course_name')
    serializer_class = SubjectCourseSerializer
    filter_fields = '__all__'
    search_fields = '__all__'


class SchedulesListView(ViewSet):
    """
    post: Returns valid schedules for classes - {"course_list": ["CSE-120", "CSE-150"], "term":"201830", "earliest_time":1000, "latest_time":2100, "gaps";"desc||asc", "days";"desc||asc", "search_full":false}
    """
    # authentication_classes = (JWTAuthentication, SessionAuthentication, BasicAuthentication)
    permission_classes = ()
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
        search_full = request.data.get('search_full', False)
        if not term:
            return Response({"Error": "No Term"})
        generator = CourseScheduler(term, earliest_time=earliest_time, latest_time=latest_time, days=days, gaps=gaps,
                                    search_full=search_full)
        courses = generator.get_valid_schedules(courses_to_search)

        return Response(courses[:65])


class CasRegistration(ViewSet):
    """
    Requires Authentication - {Authorization: "Bearer " + access_token}

    post: Registers you for classes
    example: {"crns":[123, 1234, 123], "username":"***", "password":"***", "term":201820} for summer term
    """
    # authentication_classes = (JWTAuthentication, SessionAuthentication, BasicAuthentication)
    permission_classes = ()
    renderer_classes = (JSONRenderer, BrowsableAPIRenderer)

    def retrieve(self, request, pk=None):
        return Response(None)

    def list(self, request, format=None):
        return Response(None)

    def post(self, request):
        crns = request.data.get('crns')
        if isinstance(crns, str):
            crns = crns.split(',')
        username = request.data.get('username')
        password = request.data.get('password')
        term = request.data.get('term')
        registration = CourseRegistration(course_crns=crns, term=term,
                                          auth={'username': username, 'password': password})
        response = registration.cas_login()
        if response.get('login') == 'success':
            response = registration.register()
            return Response(response)
        else:
            return Response(response)


def django_schedules_view(request):
    if request.POST:
        schedules, all_schedule_ids, all_schedule_crns, old_data = get_html_courses(request)
        return render(request, 'calendar.html',
                      {'schedules': schedules,
                       'times': {'700': '7:00am', '730': '7:30am',
                                 '800': '8:00am',
                                 '830': '8:30am', '900': '9:00am',
                                 '930': '9:30am',
                                 '1000': '10:00am', '1030': '10:30am',
                                 '1100': '11:00am', '1130': '11:30am',
                                 '1200': '12:00pm', '1230': '12:30pm',
                                 '1300': '1:00pm', '1330': '1:30pm',
                                 '1400': '2:00pm',
                                 '1430': '2:30pm',
                                 '1500': '3:00pm', '1530': '3:30pm',
                                 '1600': '4:00pm', '1630': '4:30pm',
                                 '1700': '5:00pm', '1730': '5:30pm',
                                 '1800': '6:00pm', '1830': '6:30pm',
                                 '1900': '7:00pm',
                                 '1930': '7:30pm',
                                 '2000': '8:00pm', '2030': '8:30pm',
                                 '2100': '9:00pm', '2130': '9:30pm',
                                 '2200': '10:00pm', '2230': '10:30pm', '2300': '11:00pm'},
                       'total_schedules': len(schedules)
                          , 'all_schedule_ids': all_schedule_ids, 'all_schedule_crns': all_schedule_crns,
                       'old_data': old_data})
    return render(request, 'calendar.html',
                  {'new': True, 'error': {'message': request.GET.get('error')}})


def django_saved_schedules_view(request):
    if request.POST:
        pass
    else:
        if request.user.is_authenticated:
            import json
            amount = request.GET.get('amount', 200)
            schedules = [{'courses': json.loads(str(schedule.courses)), 'term': schedule.term} for schedule in
                         Schedule.objects.filter(user=request.user).order_by('-created')[:amount]]
            schedules, all_schedule_ids, all_schedule_crns, all_schedule_terms = GetSchedules(
                schedule_crns=schedules).get_data_object()
            return render(request, 'saved_schedules.html',
                          {'schedules': schedules, 'times': {'700': '7:00am', '730': '7:30am',
                                                             '800': '8:00am',
                                                             '830': '8:30am', '900': '9:00am',
                                                             '930': '9:30am',
                                                             '1000': '10:00am', '1030': '10:30am',
                                                             '1100': '11:00am', '1130': '11:30am',
                                                             '1200': '12:00pm', '1230': '12:30pm',
                                                             '1300': '1:00pm', '1330': '1:30pm',
                                                             '1400': '2:00pm',
                                                             '1430': '2:30pm',
                                                             '1500': '3:00pm', '1530': '3:30pm',
                                                             '1600': '4:00pm', '1630': '4:30pm',
                                                             '1700': '5:00pm', '1730': '5:30pm',
                                                             '1800': '6:00pm', '1830': '6:30pm',
                                                             '1900': '7:00pm',
                                                             '1930': '7:30pm',
                                                             '2000': '8:00pm', '2030': '8:30pm',
                                                             '2100': '9:00pm', '2130': '9:30pm',
                                                             '2200': '10:00pm', '2230': '10:30pm', '2300': '11:00pm'},
                           'total_schedules': len(schedules)
                              , 'all_schedule_ids': all_schedule_ids, 'all_schedule_crns': all_schedule_crns,
                           'all_schedule_terms': all_schedule_terms})
        else:
            return render(request, 'saved_schedules.html')


def django_profile_view(request):
    if request.POST:
        if request.user.is_authenticated and request.FILES and request.FILES.get('profile_picture'):
            profile_picture = request.FILES.get('profile_picture')
            request.user.scheduleuser.profile_image = profile_picture
            request.user.scheduleuser.save()
    return render(request, 'profile.html')


def app_register_view(request):
    if request.POST:
        if not request.POST.get('password') or not request.POST.get('username'):
            return render(request, 'register.html', {'error': 'Username or Password not provided'})
        import random
        from course_api.data_managers.anonymous_names import names
        first_name = request.POST.get('first_name')
        if not first_name:
            first_name = "Anonymous"
        last_name = request.POST.get('last_name')
        if not last_name:
            last_name = random.choice(names)
        user = {'username': request.POST.get('username'), 'password': request.POST.get('password'),
                'first_name': first_name, 'last_name': last_name, 'email': request.POST.get('email')}
        if not User.objects.filter(username=request.POST.get('username')):
            user = User.objects.create_user(**user)
            login(request, user=user)
            return redirect('/app/bobcat-courses/profile')
        else:
            return render(request, 'register.html', {'error': 'username Already Exists'})
    return render(request, 'register.html')


def app_login(request):
    if request.POST and request.POST.get('username') and request.POST.get('password'):
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('/app/bobcat-courses/schedules')
        else:
            return render(request, 'login.html',
                          {'error': {'message': 'User not found, or username or password incorrect'}})
    else:
        return render(request, 'login.html')


class SaveSchedule(ViewSet):
    """
    saves schedule
    """
    authentication_classes = (JWTAuthentication, SessionAuthentication, BasicAuthentication)
    permission_classes = (IsAuthenticated,)
    renderer_classes = (JSONRenderer, BrowsableAPIRenderer)

    def retrieve(self, request, pk=None):
        return Response(None)

    def list(self, request, format=None):
        return Response(None)

    def post(self, request):
        import json
        term = request.data.get('term')
        crns = request.data.get('crns')
        if isinstance(crns, str):
            crns = crns.split(',')
        if term and crns:
            if Schedule.objects.filter(user=request.user).count() > 20:
                return Response({'error': 'Max saved schedules reached'})
            schedule = Schedule(
                user=request.user,
                term=term,
                courses=json.dumps(crns),
            )
            schedule.save()
            return Response({'success': 'Schedule Saved!'})
        return Response(None)


class DeleteSchedule(ViewSet):
    """
    saves schedule
    """
    authentication_classes = (JWTAuthentication, SessionAuthentication, BasicAuthentication)
    permission_classes = (IsAuthenticated,)
    renderer_classes = (JSONRenderer, BrowsableAPIRenderer)

    def retrieve(self, request, pk=None):
        return Response(None)

    def list(self, request, format=None):
        return Response(None)

    def post(self, request):
        print(request.data)
        import json
        term = request.data.get('term')
        crns = request.data.get('crns')
        if isinstance(crns, str):
            crns = crns.split(',')
        if term and crns:
            for schedule in Schedule.objects.filter(user=request.user, term=term):
                if set(json.loads(schedule.courses)) == set(crns):
                    schedule.delete()
                    return Response({'success': 'Schedule Deleted!'})
            return Response({'error': 'Schedule DNE (Already Deleted Probably)'})
        return Response(None)


class LoadSchedules(ViewSet):
    """
    loads users schedules ?total=30
    total = max schedules you want back
    sorted in chronological order
    """
    authentication_classes = (JWTAuthentication, SessionAuthentication, BasicAuthentication)
    permission_classes = (IsAuthenticated,)
    renderer_classes = (JSONRenderer, BrowsableAPIRenderer)

    def retrieve(self, request, pk=None):
        return Response(None)

    def list(self, request, format=None):
        import json
        amount = request.GET.get('amount', 200)
        schedules = Schedule.objects.filter(user=request.user).order_by('created')[:amount]
        schedules = [ScheduleSerializer(schedule).data for schedule in schedules]
        for schedule in schedules:
            schedule['courses'] = json.loads(schedule['courses'])
        return Response(GetSchedules(schedule_crns=schedules).get_data_object())

    def post(self, request):
        return Response(None)


class UserLoadSchedules(ViewSet):
    """
    requieres user auth
    """
    authentication_classes = (JWTAuthentication, SessionAuthentication, BasicAuthentication)
    permission_classes = (IsAuthenticated,)
    renderer_classes = (JSONRenderer, BrowsableAPIRenderer)

    def retrieve(self, request, pk=None):
        return Response(None)

    def list(self, request, format=None):
        import json
        schedules = Schedule.objects.filter(user=request.user).order_by('created')
        gen_schedules = []
        for schedule in schedules:
            courses = json.loads(schedule.courses)
            schedule = {'schedule': {}, 'info': {}}
            for course in courses:
                course_obj = Course.objects.get(crn=course)
                if course_obj.simple_name in schedule['schedule']:
                    schedule['schedule'][course_obj.simple_name][course_obj.type] = CourseSerializer(course_obj).data
                else:
                    schedule['schedule'][course_obj.simple_name] = {}
                    schedule['schedule'][course_obj.simple_name][course_obj.type] = CourseSerializer(course_obj).data
            schedule['info'] = getInfoForSchedule(schedule['schedule'])
            gen_schedules.append(schedule)
        return Response(gen_schedules)

    def post(self, request):
        return Response(None)


def user_update_script_once(request):
    for user in User.objects.all():
        user.save()
    return JsonResponse({'success': True})


def generate_scheds(request):
    if request.user.is_authenticated:
        token_jwt = RefreshToken.for_user(request.user)
        return render(request, 'schedule_search_vue.html', {'access_token': str(token_jwt.access_token)})
