from django.urls import re_path
from .consumers import ChatConsumer
from .middleware import JWTAuthMiddleware


websocket_urlpatterns = [
    re_path(r'^ws/chat/(?P<group_id>[^/]+)/$', JWTAuthMiddleware(ChatConsumer.as_asgi())),
]
