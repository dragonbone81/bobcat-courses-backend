from django.contrib.auth.models import User
from django.db.models.signals import pre_save
from course_api.models import ScheduleUser
from random import choices
from string import ascii_uppercase, digits
from django.dispatch import receiver


@receiver(pre_save, sender=User)
def save_profile(sender, instance, raw, using, update_fields, **kwargs):
    if not hasattr(instance, 'scheduleuser') or not instance.scheduleuser:
        random_key = ''.join(choices(ascii_uppercase + digits, k=25))
        instance.scheduleuser = ScheduleUser.objects.create(user=instance, unique_id=random_key)
