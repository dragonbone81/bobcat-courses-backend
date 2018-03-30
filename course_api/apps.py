from django.apps import AppConfig


class CourseApiConfig(AppConfig):
    name = 'course_api'
    verbose_name = 'Course API'

    def ready(self):
        import course_api.signals
