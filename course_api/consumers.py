from channels.generic.websocket import AsyncWebsocketConsumer
import json
from urllib import parse
from django.contrib.auth.models import AnonymousUser, User
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken
from channels.db import database_sync_to_async


class NotificationsConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        authenticated = True
        if not self.scope.get('user') or isinstance(self.scope.get('user'), AnonymousUser):
            authenticated = await self.authenticate(self.scope.get('query_string'))
        if authenticated:
            self.old_notifications = []
            await self.accept()
            await self.send(text_data=json.dumps({
                'message': 'connected'
            }))
        else:
            pass

    async def disconnect(self, close_code):
        pass

    async def authenticate(self, query):
        query = (parse.parse_qs(query.decode('utf-8')))
        auth_token = query.get('Authentication', '')[-1].split(' ')[-1]
        authentication = JWTAuthentication()
        try:
            user = authentication.get_user(authentication.get_validated_token(auth_token))
            self.scope['user'] = user
        except InvalidToken:
            await self.accept()
            await self.send(text_data=json.dumps({
                'message': 'bad_token'
            }))
            await self.close()
            return False
        return True

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'message': 'malformed_json'
            }))
            return True
        if data.get('command'):
            if data.get('command') == 'get_notifications':
                self.old_notifications = await database_sync_to_async(self.get_notifications)()
                await self.send(text_data=json.dumps({
                    'message': 'notifications_sent',
                    'data': self.old_notifications,
                }))
            elif data.get('command') == 'delete':
                await database_sync_to_async(self.delete_notification)(data.get('id'))
                self.old_notifications = await database_sync_to_async(self.get_notifications)()
                await self.send(text_data=json.dumps({
                    'message': 'notifications_sent',
                    'data': self.old_notifications,
                }))
            elif data.get('command') == 'seen_notifs':
                await database_sync_to_async(self.seen_notifications)(data.get('notifs'))
                self.old_notifications = await database_sync_to_async(self.get_notifications)()
                await self.send(text_data=json.dumps({
                    'message': 'notifications_sent',
                    'data': self.old_notifications,
                }))
            elif data.get('command') == 'ping':
                if await database_sync_to_async(self.get_notifications)() != self.old_notifications:
                    self.old_notifications = await database_sync_to_async(self.get_notifications)()
                    await self.send(text_data=json.dumps({
                        'message': 'notifications_sent',
                        'data': self.old_notifications,
                    }))

    def get_notifications(self):
        notifications = User.objects.get(username=self.scope['user'].username).notifications.notifications
        return json.loads(notifications)

    def delete_notification(self, notif_id):
        users = User.objects.get(username=self.scope['user'].username)
        notifications = json.loads(User.objects.get(username=self.scope['user'].username).notifications.notifications)
        del notifications[next((index for (index, d) in enumerate(notifications) if d["id"] == notif_id), None)]
        users.notifications.notifications = json.dumps(notifications)
        users.notifications.save()

    def seen_notifications(self, notifs_ids):
        users = User.objects.get(username=self.scope['user'].username)
        notifications = json.loads(User.objects.get(username=self.scope['user'].username).notifications.notifications)
        for notification in notifications:
            if notification.get('id') in notifs_ids:
                notification['seen'] = True
        users.notifications.notifications = json.dumps(notifications)
        users.notifications.save()
