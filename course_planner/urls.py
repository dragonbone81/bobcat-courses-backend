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
from course_api.views import course_view, CourseViewSet, CourseListView
from rest_framework import routers
from django.views.generic import RedirectView

from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework import views, serializers, status
from rest_framework.response import Response


class MessageSerializer(serializers.Serializer):
    message = serializers.CharField()


class EchoView(views.APIView):
    def post(self, request, *args, **kwargs):
        serializer = MessageSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(
            serializer.data, status=status.HTTP_201_CREATED)


router = routers.DefaultRouter()
router.register(r'courses', CourseViewSet, base_name='courses')
# router.register(r'users', ListUsers, base_name='users')
urlpatterns = [
    path('jet/', include('jet.urls', 'jet')),  # Django JET URLS
    path('admin/', admin.site.urls),
    path('', RedirectView.as_view(url='admin/')),
    path('api/courses/course-match', CourseListView.as_view()),
    path('course_pull/', course_view),
    path('api/', include(router.urls)),
    path('api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    path('api/auth/token/obtain', TokenObtainPairView.as_view()),
    path('api/auth/token/refresh', TokenRefreshView.as_view()),
    path('api/echo', EchoView.as_view())
]
