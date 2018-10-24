from django.http import JsonResponse
import json
from django.db.models import Q
from django.contrib.auth.models import User
from rest_framework import viewsets
from course_api.serializers import CourseSerializer, SubjectCourseSerializer
from django.core.mail import send_mail
from course_planner.settings import DEBUG
from course_api.utils.get_courses_base_on_simple_name import get_courses
from course_api.utils.create_notification import create_notification
from course_api.tasks import course_push_task
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_bytes
from django.template import loader
from django.contrib.auth import authenticate, login
from course_api.data_managers.uc_merced.course_scheduler import CourseScheduler
from course_api.data_managers.uc_merced.course_push import UCMercedCoursePush, SubjectClassUpdate
from course_api.models import Course, SubjectCourse, Schedule, Terms, Waitlist, Notifications
from course_api.data_managers.uc_merced.get_update_terms import update_terms as update_uc_merced_terms
from rest_framework.renderers import JSONRenderer, BrowsableAPIRenderer
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ViewSet
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.authentication import SessionAuthentication, BasicAuthentication

from rest_framework_simplejwt.tokens import RefreshToken

from django.shortcuts import render, redirect
from course_api.utils.get_schedule_info import getInfoForSchedule


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
                'first_name': request.user.first_name, 'last_name': request.user.last_name,
                'unique_id': request.user.scheduleuser.unique_id,
                'profile_image_url': request.user.scheduleuser.get_profile_image_url(),
                'email_alerts': request.user.notifications.email_alerts}
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
            return Response({"error_title": "duplicate_user",
                "error_description": "User already exists",
                "error_code": 100
            })


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
        courses_to_search = request.data.get('course_list', []) or request.data.getlist('course_list[]', [])
        term = request.data.get('term')
        if not term:
            return Response({
                "error_title": "no_term",
                "error_description": "Term not provided",
                "error_code": 101
            })
        courses = get_courses(courses_to_search, term, search_full=True)
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
            return Response({
                "error_title": "no_course_or_term",
                "error_description": "Course or term not provided",
                "error_code": 102
            })
        course = course.lower()
        course_with_dash = ''.join(course.split())
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
            course_list = course.lower().split()
            for course_filter in simple_courses:
                course_filter_list = course_filter.get('description').lower().split()
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
        school = request.GET.get('school', 'uc_merced')
        terms = Terms.objects.filter(school=school)
        if terms:
            return Response(json.loads(terms[0].terms))
        else:
            return Response({
                "error_title": "no_school",
                "error_description": "School not provided",
                "error_code": 103
            })


# Create your views here.
def course_view(request):
    if request.GET and request.GET.get('pull'):
        term = request.GET.get('term')
        UCMercedCoursePush(terms=[str(term)]).push_courses()
    elif request.GET and request.GET.get('simple'):
        SubjectClassUpdate().update_lectures()
    elif request.GET and request.GET.get('delete'):
        UCMercedCoursePush().delete_courses()
    elif request.GET and request.GET.get('terms'):
        update_uc_merced_terms()
    else:
        course_push_task()
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
    post: Returns valid schedules for classes - {"custom_events": [{event_name: "cse", start_time: 700, end_time: 830, days: "T"}], "course_list": ["CSE-120", "CSE-150"], "term":"201830", "earliest_time":1000, "latest_time":2100, "gaps";"desc||asc", "days";"desc||asc", "search_full":false, "bad_crns":[1235,345345]}
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
        bad_crns = request.data.get('bad_crns', [])
        if courses_to_search and isinstance(courses_to_search, str):
            courses_to_search = request.data.getlist('course_list', [])
            bad_crns = request.data.get('bad_crns', '').split(',')
            earliest_time = request.data.get('earliest_time', None)
            if earliest_time and earliest_time != 'any':
                earliest_time = int(earliest_time)
            else:
                earliest_time = None
            latest_time = request.data.get('latest_time', None)
            if latest_time and latest_time != 'any':
                latest_time = int(latest_time)
            else:
                latest_time = None
            filters_list = request.data.getlist('filters', [])
            gaps = 'asc'
            if 'gaps_min' in filters_list:
                gaps = 'asc'
            if 'gaps_max' in filters_list:
                gaps = 'desc'
            days = 'desc'
            if 'min_days' in filters_list:
                days = 'asc'
            if 'max_days' in filters_list:
                days = 'desc'
            search_full = False
            if 'search_full' in filters_list:
                search_full = True
            filters = True
        else:
            earliest_time = request.data.get('earliest_time', None)
            latest_time = request.data.get('latest_time', None)
            days = request.data.get('days', None)
            gaps = request.data.get('gaps', None)
            filters = request.data.get('filters', False)
            search_full = request.data.get('search_full', False)
        term = request.data.get('term', None)
        custom_events = request.data.get('custom_events', [])
        if not term:
            return Response({
                "error_title": "no_term",
                "error_description": "Term not provided",
                "error_code": 101
            })
        generator = CourseScheduler(term, earliest_time=earliest_time, latest_time=latest_time, days=days, gaps=gaps,
                                    search_full=search_full, filters=filters, bad_crns=bad_crns)
        courses = generator.get_valid_schedules(courses_to_search, custom_events=custom_events)
        return Response(courses[:80])


class ContactUs(ViewSet):
    """

    post: username, email, name, message
    Sends Email to us with the message and stuff
    """
    # authentication_classes = (JWTAuthentication, SessionAuthentication, BasicAuthentication)
    permission_classes = ()
    renderer_classes = (JSONRenderer, BrowsableAPIRenderer)

    def retrieve(self, request, pk=None):
        return Response(None)

    def list(self, request, format=None):
        return Response(None)

    def post(self, request):
        username = request.data.get('username')
        email = request.data.get('email')
        name = request.data.get('name')
        message = request.data.get('message')
        send_mail('User {} submitted a comment, username:{}, email:{}'.format(name, username, email), message,
                  'support@bobcat-courses.com',
                  ['mmoison@ucmerced.edu', 'mhernandez268@ucmerced.edu',
                   'cvernikoff@ucmerced.edu'],
                  fail_silently=True)
        return Response({'success': True})


class UpdateNotificationSettings(ViewSet):
    """

    post: email_alerts !!AND!! email
    Just sets the users values to the ones given
    """
    authentication_classes = (JWTAuthentication, SessionAuthentication, BasicAuthentication)
    permission_classes = ()
    renderer_classes = (JSONRenderer, BrowsableAPIRenderer)

    def retrieve(self, request, pk=None):
        return Response(None)

    def list(self, request, format=None):
        return Response(None)

    def post(self, request):
        email_alerts = request.data.get('email_alerts')
        email = request.data.get('email')
        request.user.notifications.email_alerts = email_alerts
        request.user.email = email
        request.user.notifications.save()
        request.user.save()
        return Response({'success': True})


def django_schedules_view(request):
    if request.GET and request.GET.get('term') and request.GET.getlist('courses'):
        term = request.GET.get('term')
        courses = request.GET.get('courses').split(',')
        return render(request, 'plan_schedule.html', {'courses': courses, 'term': term})
    return render(request, 'plan_schedule.html')


def django_saved_schedules_view(request):
    return render(request, 'saved_schedules.html',
                  {'access_token': str(RefreshToken.for_user(request.user).access_token)})


def django_waitlist_view(request):
    return render(request, 'waitlist.html', {})


def django_profile_view(request):
    message = {}
    if request.POST:
        if request.user.is_authenticated and request.FILES and request.FILES.get('profile_picture'):
            profile_picture = request.FILES.get('profile_picture')
            request.user.scheduleuser.profile_image = profile_picture
            request.user.scheduleuser.save()
            message = {'success': {'message': 'Profile image updated.'}}
        elif request.user.is_authenticated:
            if 'unsubscribe' in request.POST:
                request.user.notifications.email_alerts = False
                request.user.notifications.save()
                message = {'success': {'message': 'You are now unsubscribed and will not get anymore emails.'}}
            if 'subscribe' in request.POST:
                if request.POST.get('email', ''):
                    request.user.email = request.POST.get('email', '')
                    request.user.save()
                request.user.notifications.email_alerts = True
                request.user.notifications.save()
                message = {'success': {
                    'message': 'You are now subscribed and will receive emails and waitlist notifications.'}}
            elif 'update_email' in request.POST:
                request.user.email = request.POST.get('email', '')
                request.user.save()
                message = {'success': {'message': 'Your email has been updated, {}.'.format(request.user.email)}}
    return render(request, 'profile.html', message)


def app_register_view(request):
    if request.POST:
        if not request.POST.get('password') or not request.POST.get('username'):
            return render(request, 'register.html', {'error': {'message': 'Username or Password not provided'}})
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
            return render(request, 'register.html', {'error': {'message': 'Username Already Exists'}})
    return render(request, 'register.html')


def app_privacy_view(request):
    return render(request, 'privacy.html')


def app_about_view(request):
    if request.POST:
        if not request.user.is_authenticated:
            username = None
            name = request.POST.get('name', "Anonymous")
            email = request.POST.get('email', "blank@blank.com")
        else:
            username = request.user.username
            name = request.user.get_full_name() or request.POST.get('name', "Anonymous") or request.user.username
            email = request.user.email or request.POST.get('email', "blank@blank.com")
        message = request.POST.get('message')
        send_mail('User {} submitted a comment, username:{}, email:{}'.format(name, username, email), message,
                  'support@bobcat-courses.com',
                  ['mmoison@ucmerced.edu', 'mhernandez268@ucmerced.edu', 'fdietz@ucmerced.edu',
                   'cvernikoff@ucmerced.edu'],
                  fail_silently=True)
    return render(request, 'about.html')


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


def app_reset_password(request):
    if request.user and request.POST.get('old_password') and request.POST.get('new_password'):
        if request.user.check_password(request.POST.get('old_password')):
            request.user.set_password(request.POST.get('new_password'))
            request.user.save()
            login(request, request.user)
            return redirect('/app/bobcat-courses/schedules')
        else:
            return render(request, 'change_password.html', {'error': {'message': 'Old password was incorrect'}})
    return render(request, 'change_password.html')


class SaveSchedule(ViewSet):
    """
    saves schedule
    Needs user authentication and saves schedule to that user
    post term, crns:['34454', '45556',...], hasConflictingFinals:false,
    "custom_events":[{event_name: "Work", start_time: 700, end_time: 730, days: "WM"}]
    if schedule already exists {'schedule_index': index, 'error': 'Schedule already exists', 'type': 'already_exists'}
    if user has more than 20 saved schedules, returns {'error': 'Max saved schedules reached'}
    """
    authentication_classes = (JWTAuthentication, SessionAuthentication, BasicAuthentication)
    permission_classes = (IsAuthenticated,)
    renderer_classes = (JSONRenderer, BrowsableAPIRenderer)

    def retrieve(self, request, pk=None):
        return Response(None)

    def list(self, request, format=None):
        return Response(None)

    def post(self, request):
        term = request.data.get('term')
        crns = request.data.get('crns')
        user_events = request.data.get('custom_events', [])
        if isinstance(crns, str):
            crns = crns.split(',')
        if term and crns and len(crns) > 0 and crns[0] != '':
            user_schedules = Schedule.objects.filter(user=request.user)
            if user_schedules.count() > 20:
                return Response({'error': 'Max saved schedules reached'})
            # check Users schedules to make sure schedule not already saved
            for index, schedule in enumerate(user_schedules):
                if set(crns) == set(json.loads(schedule.courses)):
                    same_events = True
                    if len(json.loads(schedule.user_events)) != len(user_events):
                        same_events = False
                    else:
                        schedule_events = json.loads(schedule.user_events)
                        for event in user_events:
                            if not any(d['event_name'] == event['event_name'] and d['start_time'] == event[
                                'start_time'] and d['end_time'] == event['end_time'] and d['days'] == event['days'] for
                                       d in schedule_events):
                                same_events = False
                                break
                    if same_events:
                        return Response(
                            {'schedule_index': index,
                                "error_title": "schedule_already_exists",
                                "error_description": "The schedule being saved already exists",
                                "error_code": 104
                            })
            schedule = Schedule(
                user=request.user,
                term=term,
                courses=json.dumps(crns),
                user_events=json.dumps(user_events),
                finals_conflict=request.data.get('hasConflictingFinals', False)
            )
            schedule.save()
            return Response({'success': True})
        return Response({
                        "error_title": "schedule_limit_reached",
                        "error_description": "The limit of saved schedules was reached",
                        "error_code": 112
                        })


# class StarSchedule(ViewSet):
#     """
#     star schedule
#     Needs user authentication and saves schedule to that user
#     post term, crns:['34454', '45556',...], star
#     if user has more than 20 saved schedules, returns {'error': 'Max saved schedules reached'}
#     """
#     authentication_classes = (JWTAuthentication, SessionAuthentication, BasicAuthentication)
#     permission_classes = (IsAuthenticated,)
#     renderer_classes = (JSONRenderer, BrowsableAPIRenderer)
#
#     def retrieve(self, request, pk=None):
#         return Response(None)
#
#     def list(self, request, format=None):
#         return Response(None)
#
#     def post(self, request):
#         term = request.data.get('term')
#         crns = request.data.get('crns')
#         if isinstance(request.data.get('star'), str):
#             star = True if request.POST.get("star") == "true" else False
#         else:
#             star = request.data.get('star')
#         if isinstance(crns, str):
#             crns = crns.split(',')
#         if term and crns:
#             for schedule in Schedule.objects.filter(user=request.user, term=term):
#                 if set(json.loads(schedule.courses)) == set(crns):
#                     schedule.important = star
#                     schedule.save()
#                     if star:
#                         return Response({'success': 'Schedule favorited.'})
#                     else:
#                         return Response({'success': 'Schedule un-favorited.'})
#             return Response({'error': 'Ummmm...please contact us by clicking on the footer :*('})
#         return Response(None)


class DeleteSchedule(ViewSet):
    """
    saves schedule
    Needs user authentication and deletes that users schedule
    post term, crns:['34454', '45556',...] <-of schedule you want to delete ,
    "custom_events":[{event_name: "Work", start_time: 700, end_time: 730, days: "WM"}]
    if schedule not found returns {'error': 'Schedule DNE (Already Deleted Probably)'}
    """
    authentication_classes = (JWTAuthentication, SessionAuthentication, BasicAuthentication)
    permission_classes = (IsAuthenticated,)
    renderer_classes = (JSONRenderer, BrowsableAPIRenderer)

    def retrieve(self, request, pk=None):
        return Response(None)

    def list(self, request, format=None):
        return Response(None)

    def post(self, request):
        term = request.data.get('term')
        crns = request.data.get('crns')
        user_events = request.data.get('custom_events', [])
        if isinstance(crns, str):
            crns = crns.split(',')
        if term and crns:
            for schedule in Schedule.objects.filter(user=request.user, term=term):
                if set(json.loads(schedule.courses)) == set(crns):
                    same_events = True
                    if len(json.loads(schedule.user_events)) != len(user_events):
                        same_events = False
                    else:
                        schedule_events = json.loads(schedule.user_events)
                        for event in user_events:
                            if not any(d['event_name'] == event['event_name'] and d['start_time'] == event[
                                'start_time'] and d['end_time'] == event['end_time'] and d['days'] == event['days'] for
                                       d in schedule_events):
                                same_events = False
                                break
                    if same_events:
                        schedule.delete()
                        return Response({'success': True})
            return Response({
                "error_title": "schedule_dne",
                "error_description": "Could not find schedule",
                "error_code": 105
            })
        return Response({
            "error_title": "no_term_or_crns",
            "error_description": "Terms or CRN's not provided",
            "error_code": 106
        })


class ProfileImageUpload(ViewSet):
    """
    Auth required
    post with image as a field (profile_image)
    """
    authentication_classes = (JWTAuthentication, SessionAuthentication, BasicAuthentication)
    permission_classes = (IsAuthenticated,)
    renderer_classes = (JSONRenderer, BrowsableAPIRenderer)

    def retrieve(self, request, pk=None):
        return Response(None)

    def list(self, request, format=None):
        return Response(None)

    def post(self, request):
        if request.data.get('profile_image'):
            request.user.scheduleuser.profile_image = request.data.get('profile_image')
            request.user.scheduleuser.save()
            return Response({'success': True, 'image_url': request.user.scheduleuser.get_profile_image_url()})
        return Response({
            "error_title": "no_image",
            "error_description": "Image not provided",
            "error_code": 111
        })


class UserLoadSchedules(ViewSet):
    """
    Just requires user auth and returns all schedules the user has saved
    """
    authentication_classes = (JWTAuthentication, SessionAuthentication, BasicAuthentication)
    permission_classes = (IsAuthenticated,)
    renderer_classes = (JSONRenderer, BrowsableAPIRenderer)

    def retrieve(self, request, pk=None):
        return Response(None)

    def list(self, request, format=None):
        if request.GET.get('term'):
            schedules = Schedule.objects.filter(user=request.user, term=request.GET.get('term')).order_by('-created')
        else:
            schedules = Schedule.objects.filter(user=request.user).order_by('-created')
        gen_schedules = []
        terms = json.loads(Terms.objects.get(school='uc_merced').terms)
        for schedule in schedules:
            if schedule.term not in terms:
                schedule.delete()
            else:
                courses = json.loads(schedule.courses)
                custom_events = json.loads(schedule.user_events)
                schedule_dict = {'schedule': {}, 'info': {}}
                courses = Course.objects.filter(crn__in=courses)
                if custom_events:
                    schedule_dict['schedule']['custom_events'] = [course for course in custom_events]
                for course in courses:
                    if course.simple_name in schedule_dict['schedule']:
                        schedule_dict['schedule'][course.simple_name].append(course.to_dict())
                    else:
                        schedule_dict['schedule'][course.simple_name] = []
                        schedule_dict['schedule'][course.simple_name].append(course.to_dict())
                schedule_dict['info'] = getInfoForSchedule(schedule_dict['schedule'])
                schedule_dict['custom_events'] = schedule_dict['schedule'].get('custom_events', [])
                if schedule_dict['schedule'].get('custom_events'):
                    del schedule_dict['schedule']['custom_events']
                schedule_dict['info']['term'] = schedule.term
                schedule_dict['info']['hasConflictingFinals'] = schedule.finals_conflict
                gen_schedules.append(schedule_dict)
        return Response(gen_schedules)

    def post(self, request):
        return Response(None)


def user_update_script_once(request):
    for user in User.objects.all():
        notifications = json.loads(user.notifications.notifications)
        for notification in notifications:
            if not notification.get('email_sent'):
                notification['email_sent'] = False
            if not notification.get('time'):
                import datetime
                from django.utils import dateformat
                notification['time'] = dateformat.format(datetime.datetime.now(), 'F j, Y, P')
        user.notifications.notifications = json.dumps(notifications)
        user.notifications.save()
        user.save()
    return JsonResponse({'success': True})


class PasswordChange(ViewSet):
    """
    changes the users password requires current sign in and auth
    also requires {"old_password":"abc123", "new_password":"xyz789"}

    returns {'success': True}, {'fail': 'password_incorrect'}, {'fail': 'incorrect_data'}


    """
    authentication_classes = (JWTAuthentication, SessionAuthentication, BasicAuthentication)
    permission_classes = (IsAuthenticated,)
    renderer_classes = (JSONRenderer, BrowsableAPIRenderer)

    def retrieve(self, request, pk=None):
        return Response(None)

    def list(self, request, format=None):
        return Response(None)

    def post(self, request):
        if request.user and request.data.get('old_password') and request.data.get('new_password'):
            if request.user.check_password(request.data.get('old_password')):
                request.user.set_password(request.data.get('new_password'))
                request.user.save()
                return Response({'success': True})
            else:
                return Response({
                    "error_title": "incorrect_password",
                    "error_description": "Old passwords do not match",
                    "error_code": 107
                })
        else:
            return Response({
                "error_title": "passwords_not_provided",
                "error_description": "Passwords not provided",
                "error_code": 108
            })


def forgot_password_process(request):
    associated_user = User.objects.filter(username=request.data.get('username'))
    if associated_user.exists() and associated_user[0] and associated_user[0].email:
        user = associated_user[0]
        subject = 'Your Password Reset Link for BobcatCourses'
        url = ('https://' if not DEBUG else 'http://') + request.get_host() \
              + '/app/bobcat-courses/reset_password_confirm/' + urlsafe_base64_encode(
            force_bytes(user.pk)).decode("utf-8") + '-' + default_token_generator.make_token(user)
        email = loader.render_to_string('forgot_password/reset_password_email.html',
                                        {'username': user.username,
                                         'link': url})
        send_mail(subject, email, 'support@bobcat-courses.com', [user.email], html_message=email,
                  fail_silently=False)
        return Response({'success': True})
    return Response({
        "error_title": "user_does_not_exist",
        "error_description": "Provided user does not exist",
        "error_code": 109
    })


class ForgotPassword(ViewSet):
    """
    {"username":"cvernikoff"}
    returns {'success': True}, {'success': False}
    """
    # authentication_classes = (JWTAuthentication, SessionAuthentication, BasicAuthentication)
    permission_classes = ()
    renderer_classes = (JSONRenderer, BrowsableAPIRenderer)

    def retrieve(self, request, pk=None):
        return Response(None)

    def list(self, request, format=None):
        return Response(None)

    def post(self, request):
        return forgot_password_process(request)


def password_forgot_start(request):
    if request.POST:
        request.data = request.POST
        response = forgot_password_process(request)
        if not response.data.get('success'):
            return render(request, 'forgot_password/forgot_password_start.html',
                          {'error': {'message': 'Your account does not have a registered email'}})
        return render(request, 'forgot_password/forgot_password_start.html',
                      {'success': {'message': 'Check your email'}})
    else:
        return render(request, 'forgot_password/forgot_password_start.html')


def password_reset_confirm(request, uidb64=None, token=None):
    try:
        uid = urlsafe_base64_decode(uidb64)
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None
    if user is not None and default_token_generator.check_token(user, token):
        if request.POST:
            new_password = request.POST.get('new_password')
            user.set_password(new_password)
            user.save()
            return redirect('https://bobcatcourses.tk/login')
        else:
            return render(request, 'forgot_password/password-forgot-reset.html')
    else:
        return render(request, 'forgot_password/password-forgot-reset.html',
                      {'error': {'message': 'Are you sure this link is valid? Check your email again.'}})


def waitlist_check(request):
    waitlists = Waitlist.objects.all().prefetch_related('users').select_related('course')
    for waitlist in waitlists:
        if not waitlist.expired and waitlist.course.available > 0 or waitlist.expired and waitlist.course.available <= 0:
            if not waitlist.expired and waitlist.course.available > 0:
                message = 'open_course'
                waitlist.expired = True
            elif waitlist.expired and waitlist.course.available <= 0:
                message = 'closed_course'
                waitlist.expired = False
            else:
                # this should not happen but just to satisfy the logic checker
                message = 'none'
            for user in waitlist.users.all():
                notifications = json.loads(user.notifications.notifications)
                notif_id = 0
                if notifications:
                    notif_id = notifications[-1].get('id') + 1
                new_notification = create_notification(notif_type='waitlist', notif_id=notif_id,
                                                       data={'message': message, 'course': waitlist.course.to_dict()})
                notifications.append(new_notification)
                user.notifications.notifications = json.dumps(notifications)
                user.notifications.save()
            waitlist.save()
    [waitlist.delete() for waitlist in waitlists if waitlist.users.count() == 0]
    return JsonResponse({})


def notification_check(request):
    for notification in Notifications.objects.all().select_related('user'):
        if notification.user.email:
            notifications = json.loads(notification.notifications)
            for notification_dict in notifications:
                if not notification_dict.get('email_sent', False):
                    email = loader.render_to_string('notifications/notification_email.html',
                                                    {'type': notification_dict.get('type'),
                                                     'message': notification_dict.get('data', {}).get('message'),
                                                     'course': notification_dict.get('data', {}).get('course'),
                                                     'link': ('https://' if not DEBUG else 'http://') +
                                                             request.get_host() + '/app/bobcat-courses/profile'
                                                     })
                    if notification_dict.get('type') == 'waitlist':
                        subject = 'BobcatCourses Waitlist Alert'
                    else:
                        subject = 'BobcatCourses Message'
                    send_mail(subject,
                              email,
                              'notifications@bobcat-courses.com',
                              [notification.user.email],
                              html_message=email,
                              fail_silently=True)
                    notification_dict['email_sent'] = True
            notification.notifications = json.dumps(notifications)
            notification.save()
    return JsonResponse({})


class NotificationsViewSet(ViewSet):
    """
    RequiresAuth
    get:
        command: delete, id: (notification_id) --> deleted notification from user
        command: seen_notifs, notifs: [0,5,3] --> marks notifications with ids as seen
    post:
        crn: 123464 --> add user to a waitlist with that crn and generate notif
    """
    authentication_classes = (JWTAuthentication, SessionAuthentication, BasicAuthentication)
    permission_classes = (IsAuthenticated,)
    renderer_classes = (JSONRenderer, BrowsableAPIRenderer)

    def retrieve(self, request, pk=None):
        return Response(None)

    def list(self, request, format=None):
        if request.GET.get('command'):
            command = request.GET.get('command')
            if command == 'delete':
                notif_id = request.GET.get('id')
                notifications = json.loads(request.user.notifications.notifications)
                del notifications[
                    next((index for (index, d) in enumerate(notifications) if d["id"] == int(notif_id)), None)]
                request.user.notifications.notifications = json.dumps(notifications)
                request.user.notifications.save()
            elif command == 'seen_notifs':
                notifs_ids = json.loads(request.GET.get('notifs'))
                notifications = json.loads(request.user.notifications.notifications)
                for notification in notifications:
                    if notification.get('id') in notifs_ids:
                        notification['seen'] = True
                request.user.notifications.notifications = json.dumps(notifications)
                request.user.notifications.save()
        return Response(json.loads(request.user.notifications.notifications))

    def post(self, request):
        if request.data.get('crn'):
            waitlist, created = Waitlist.objects.get_or_create(school='uc_merced',
                                                               course=Course.objects.get(crn=request.data.get('crn')))
            waitlist.users.add(request.user)
            waitlist.save()
            notifications = json.loads(request.user.notifications.notifications)
            notif_id = 0
            if notifications:
                notif_id = notifications[-1].get('id') + 1

            notifications.append(
                create_notification(notif_type='message', notif_id=notif_id, data={
                    'message': 'You will be notified when course {} is open'.format(request.data.get('crn'))}))
            request.user.notifications.notifications = json.dumps(notifications)
            request.user.notifications.save()
            return Response({'success': True})
        return Response({
            "error_title": "no_crn",
            "error_description": "CRN not provided",
            "error_code": 110
        })


class WaitlistViewSet(ViewSet):
    """
    RequiresAuth
    post: crn - removes user from waitlist
    """
    authentication_classes = (JWTAuthentication, SessionAuthentication, BasicAuthentication)
    permission_classes = (IsAuthenticated,)
    renderer_classes = (JSONRenderer, BrowsableAPIRenderer)

    def retrieve(self, request, pk=None):
        return Response(None)

    def list(self, request, format=None):
        waitlists = Waitlist.objects.filter(users__in=[request.user]).select_related('course').prefetch_related('users')
        response = [{
            'course': waitlist.course.to_dict(),
            'users': waitlist.users.count(),
        } for waitlist in waitlists]
        return Response(response)

    def post(self, request):
        if request.data.get('crn'):
            waitlist = Waitlist.objects.get(course=request.data.get('crn'))
            waitlist.users.remove(request.user)
            waitlist.save()
            return Response({'success': True})
        return Response({
            "error_title": "no_crn",
            "error_description": "CRN not provided",
            "error_code": 110
        })


def page_not_found(request, exception):
    return render(request, 'errors/404.html')


def error_500(request):
    return render(request, 'errors/500.html')
