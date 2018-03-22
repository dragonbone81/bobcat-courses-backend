from rest_framework import serializers
from course_api.models import Course, Schedule


class CourseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Course
        fields = '__all__'


class ScheduleSerializer(serializers.ModelSerializer):
    # import json
    courses = serializers.CharField()

    class Meta:
        model = Schedule
        fields = '__all__'
