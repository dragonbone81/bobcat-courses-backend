from django.contrib.auth.models import User
from django.db.models.signals import post_save
from course_api.models import ScheduleUser, Notifications
from random import choices
from string import ascii_uppercase, digits
from django.dispatch import receiver
from json import dumps as json_dumps


@receiver(post_save, sender=User)
def save_profile(sender, instance, raw, using, update_fields, **kwargs):
    if not hasattr(instance, 'scheduleuser') or not instance.scheduleuser:
        random_key = ''.join(choices(ascii_uppercase + digits, k=25))
        instance.scheduleuser = ScheduleUser.objects.create(user=instance, unique_id=random_key)
    if not hasattr(instance, 'notifications') or not instance.notifications:
        instance.notifications = Notifications.objects.create(
            user=instance,
            notifications=json_dumps([
                {'seen': False, 'type': 'message', 'id': 0, 'data': {'message': 'Welcome to BobcatCourses'}}
            ])
        )
