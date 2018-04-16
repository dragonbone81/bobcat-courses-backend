"""course_planner URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include, re_path
from course_api.views import course_view, CourseViewSet, CourseListView, ExampleJWT, UserInfo, UserRegistration, \
    CoursesSearch, SchedulesListView, CasRegistration, django_schedules_view, GetTerms, app_login, SaveSchedule, \
    django_saved_schedules_view, django_profile_view, app_register_view, DeleteSchedule, \
    user_update_script_once, ping, UserLoadSchedules, SubjectCourseViewSet, app_about_view, StarSchedule, \
    PasswordChange, app_reset_password, ForgotPassword, password_reset_confirm, password_forgot_start, page_not_found, \
    error_500
from rest_framework import routers
from django.views.generic import RedirectView
from django.contrib.auth.views import logout
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from django.conf.urls import handler404, handler500

router = routers.DefaultRouter()
router.register(r'courses-list', CourseViewSet, base_name='courses')
router.register(r'register', UserRegistration, base_name='register')
router.register(r'courses/course-match', CourseListView, base_name='CourseListView')
router.register(r'courses/schedule-search', SchedulesListView, base_name='SchedulesListView')
router.register(r'courses/course-search', CoursesSearch, base_name='CoursesSearch')
router.register(r'courses/course-dump', SubjectCourseViewSet, base_name='SubjectCourseViewSet')
router.register(r'courses/course-register', CasRegistration, base_name='CasRegistration')
router.register(r'courses/get-terms', GetTerms, base_name='GetTerms')
router.register(r'users/save-schedule', SaveSchedule, base_name='SaveSchedule')
router.register(r'users/star-schedule', StarSchedule, base_name='StarSchedule')
router.register(r'users/schedule-dump', UserLoadSchedules, base_name='UserLoadSchedules')
router.register(r'users/user-info', UserInfo, base_name='user-info')
router.register(r'users/delete-schedule', DeleteSchedule, base_name='DeleteSchedule')
router.register(r'users/change-password', PasswordChange, base_name='PasswordChange')
router.register(r'users/forgot-password', ForgotPassword, base_name='ForgotPassword')
handler404 = page_not_found
handler500 = error_500
urlpatterns = [
    path('jet/', include('jet.urls', 'jet')),  # Django JET URLS
    path('admin/', admin.site.urls),
    path('api/courses/jwt-example', ExampleJWT.as_view()),
    path('course_pull/', course_view),
    path('api/', include(router.urls)),
    path('api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    path('api/auth/token/obtain', TokenObtainPairView.as_view()),
    path('api/auth/token/refresh', TokenRefreshView.as_view()),
    path('sync_users', user_update_script_once),
    path('api/oauth/', include('social_django.urls', namespace='social')),

    # local schedule urls
    path('', RedirectView.as_view(url='/app/bobcat-courses/schedules')),
    path('api/calendar', RedirectView.as_view(url='/app/bobcat-courses')),
    path('app/bobcat-courses', RedirectView.as_view(url='/app/bobcat-courses/schedules')),
    path('app/bobcat-courses/schedules', django_schedules_view),
    path('app/bobcat-courses/profile', django_profile_view),
    path('app/bobcat-courses/saved-schedules', django_saved_schedules_view),
    path('app/bobcat-courses/register', app_register_view),
    path('app/bobcat-courses/login', app_login),
    path('app/bobcat-courses/logout', logout, {'next_page': '/app/bobcat-courses/schedules'}),
    path('app/bobcat-courses/about', app_about_view),
    path('app/bobcat-courses/reset-password', app_reset_password),
    path('app/bobcat-courses/forgot-password', password_forgot_start),
    re_path('app/bobcat-courses/reset_password_confirm/(?P<uidb64>[0-9A-Za-z]+)-(?P<token>.+)/$',
            password_reset_confirm,
            name='reset_password_confirm'),

    # ping url
    path('api/ping', ping),
]
