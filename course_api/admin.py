from django.contrib import admin
from course_api.models import Course


# Register your models here.
class CourseAdmin(admin.ModelAdmin):
    # list_display = ('crn', 'subject', 'course_name')
    # search_fields = ['crn', 'subject', 'course_name']
    pass


admin.site.register(Course)
