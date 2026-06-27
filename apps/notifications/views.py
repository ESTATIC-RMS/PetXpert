from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from .models import Notification
from .serializers import NotificationSerializer

class NotificationListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        unread_only = request.query_params.get('unread', 'false').lower() == 'true'
        queryset = Notification.objects.filter(recipient=request.user)
        if unread_only:
            queryset = queryset.filter(is_read=False)
        
        # Limit to last 50 notifications
        queryset = queryset[:50]
        serializer = NotificationSerializer(queryset, many=True)
        return Response(serializer.data)

class NotificationMarkAllReadView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        Notification.objects.filter(recipient=request.user, is_read=False).update(is_read=True)
        return Response({'success': True, 'message': 'All notifications marked as read.'})

class NotificationMarkReadView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, notification_id):
        try:
            notification = Notification.objects.get(id=notification_id, recipient=request.user)
            notification.is_read = True
            notification.save(update_fields=['is_read'])
            return Response({'success': True, 'message': 'Notification marked as read.'})
        except Notification.DoesNotExist:
            return Response({'error': 'Notification not found'}, status=status.HTTP_404_NOT_FOUND)
