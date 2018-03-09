from django.contrib import admin
from course_api.models import Course, Schedule, SubjectClass


# Register your models here.
class CourseAdmin(admin.ModelAdmin):
    list_display = ('crn', 'subject', 'type', 'course_name', 'course_id', 'course_name', 'course_name',)
    search_fields = ['crn', 'subject', 'type', 'course_name', 'course_id', 'course_name', 'course_name', ]


class ScheduleAdmin(admin.ModelAdmin):
    list_display = ('user',)
    search_fields = ['user__username', 'user__first_name', 'user__last_name', ]


class SubjectClassAdmin(admin.ModelAdmin):
    list_display = ('course_name',)
    search_fields = ('course_name',)


admin.site.register(Course, CourseAdmin)
admin.site.register(Schedule, ScheduleAdmin)
admin.site.register(SubjectClass, SubjectClassAdmin)
