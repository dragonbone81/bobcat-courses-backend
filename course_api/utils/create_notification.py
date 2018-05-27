import datetime
from django.utils import dateformat


def create_notification(notif_type, notif_id, data):
    return {'seen': False,
            'email_sent': False,
            'type': notif_type,
            'id': notif_id,
            'data': data,
            'time': dateformat.format(datetime.datetime.now(), 'F j, Y, P'),
            }
