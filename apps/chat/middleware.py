from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError


User = get_user_model()


@database_sync_to_async
def get_user_from_token(token):
    """
    Authenticate user from JWT token.
    """
    try:
        jwt_auth = JWTAuthentication()
        validated_token = jwt_auth.get_validated_token(token)
        user = jwt_auth.get_user(validated_token)
        return user
    except (InvalidToken, TokenError):
        return None


class JWTAuthMiddleware:
    """
    Middleware to authenticate WebSocket connections using JWT token from query string.
    """

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        # Extract token from query string
        query_string = scope.get('query_string', b'').decode()
        token = None
        
        if query_string:
            from urllib.parse import parse_qs
            params = parse_qs(query_string)
            token = params.get('token', [None])[0]
        
        if token:
            user = await get_user_from_token(token)
            if user:
                scope['user'] = user
            else:
                scope['user'] = None
        else:
            scope['user'] = None
        
        return await self.app(scope, receive, send)
