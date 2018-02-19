from django.contrib import admin
from course_api.models import Course


# Register your models here.
class CourseAdmin(admin.ModelAdmin):
    list_display = ('crn', 'subject', 'type', 'course_name')
    search_fields = ['crn', 'subject', 'type', 'course_name']


admin.site.register(Course, CourseAdmin)
