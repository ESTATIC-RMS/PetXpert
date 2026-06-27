from django.urls import path
from .views import (
    NotificationListView, NotificationMarkAllReadView, NotificationMarkReadView
)

urlpatterns = [
    path('', NotificationListView.as_view(), name='notification_list'),
    path('mark-all-read/', NotificationMarkAllReadView.as_view(), name='notification_mark_all_read'),
    path('<uuid:notification_id>/mark-read/', NotificationMarkReadView.as_view(), name='notification_mark_read'),
]
