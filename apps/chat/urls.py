from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import MessageViewSet, ChatGroupViewSet

router = DefaultRouter()
router.register(r'groups', ChatGroupViewSet, basename='chatgroup')
router.register(r'(?P<group_id>[^/]+)/messages', MessageViewSet, basename='message')

urlpatterns = [
    path('', include(router.urls)),
]
