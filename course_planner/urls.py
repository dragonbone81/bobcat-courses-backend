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
from django.urls import path, include
from course_api.views import course_view, CourseViewSet, CourseListView, ExampleJWT, UserInfo, UserRegistration, \
    CoursesSearch, SchedulesListView, CasRegistration, calendar, GetTerms, django_login
from rest_framework import routers
from django.views.generic import RedirectView
from django.contrib.auth.views import logout
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

router = routers.DefaultRouter()
router.register(r'courses-list', CourseViewSet, base_name='courses')
router.register(r'login', UserInfo, base_name='login')
router.register(r'register', UserRegistration, base_name='register')
router.register(r'courses/course-match', CourseListView, base_name='CourseListView')
router.register(r'courses/schedule-search', SchedulesListView, base_name='SchedulesListView')
router.register(r'courses/course-search', CoursesSearch, base_name='CoursesSearch')
router.register(r'courses/course-register', CasRegistration, base_name='CasRegistration')
router.register(r'courses/get-terms', GetTerms, base_name='GetTerms')
urlpatterns = [
    path('jet/', include('jet.urls', 'jet')),  # Django JET URLS
    path('admin/', admin.site.urls),
    path('', RedirectView.as_view(url='admin/')),
    path('api/courses/jwt-example', ExampleJWT.as_view()),
    path('course_pull/', course_view),
    path('api/', include(router.urls)),
    path('api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    path('api/auth/token/obtain', TokenObtainPairView.as_view()),
    path('api/auth/token/refresh', TokenRefreshView.as_view()),
    path('api/django/logout', logout, {'next_page': '/api/calendar'}),
    path('api/django/login', django_login),

    # local schedule urls
    path('api/calendar', RedirectView.as_view(url='/app/bobcat-courses')),
    path('app/bobcat-courses', RedirectView.as_view(url='/app/bobcat-courses/schedules')),
    path('app/bobcat-courses/schedules', calendar),
    path('app/bobcat-courses/profile', calendar),
    path('app/bobcat-courses/saved-schedules', calendar)
]
