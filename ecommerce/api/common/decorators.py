from functools import wraps
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings
from jwt import DecodeError, ExpiredSignatureError
import jwt

# Decorator to verify the access token


def verify_access_token(func):
    @wraps(func)
    def wrapper(request, *args, **kwargs):
        # Get the token from the Authorization header
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer'):
            return Response({'success': False, 'message': 'Authorization header is missing or malformed'}, status=status.HTTP_401_UNAUTHORIZED)

        # Extract the token from the header
        try:
            token = auth_header.split(' ')[1]
        except IndexError:
            return Response({'success': False, 'message': 'Token is missing'}, status=status.HTTP_401_UNAUTHORIZED)

        # Decode the token
        try:
            decoded_data = jwt.decode(token, settings.SECRET_KEY, algorithms=[
                                      'HS256'])
            request.user = decoded_data
        except (DecodeError, ExpiredSignatureError):
            return Response({'success': False, 'message': 'Invalid or expired token'}, status=status.HTTP_401_UNAUTHORIZED)

        return func(request, *args, **kwargs)
    return wrapper


# Decorator to verify the admin access
def verify_admin(func):
    @wraps(func)
    def wrapper(request, *args, **kwargs):
        if 'role' not in request.user or request.user['role'] != '1999':
            return Response({'success': False, 'message': 'Permission denied. Admin access required.'}, status=status.HTTP_403_FORBIDDEN)
        return func(request, *args, **kwargs)
    return wrapper
