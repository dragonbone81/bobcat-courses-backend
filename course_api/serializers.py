from rest_framework import serializers
from course_api.models import Course, Schedule, SubjectCourse


class CourseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Course
        fields = '__all__'


class ScheduleSerializer(serializers.ModelSerializer):
    courses = serializers.CharField()

    class Meta:
        model = Schedule
        fields = '__all__'


class SubjectCourseSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubjectCourse
        fields = '__all__'
