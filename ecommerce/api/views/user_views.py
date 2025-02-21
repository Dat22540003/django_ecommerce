from api.services.user_services import UserServices
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from api.common.utils import convert_to_json_compatible, send_email, generate_access_token, generate_refresh_token, generate_password_reset_token, upload_single_image
from api.common.decorators import verify_access_token, verify_admin
import jwt
from django.conf import settings
import base64
import threading
from django.utils.crypto import get_random_string
from time import sleep
from django.contrib.auth.hashers import make_password, check_password
from bson import ObjectId
from datetime import datetime


def delete_temp_user(email):
    sleep(300)
    UserServices().delete_user(email)


# Register a user
@api_view(['POST'])
def register(request):
    data = request.data
    email = data.get('email')
    password = data.get('password')
    firstname = data.get('firstname')
    lastname = data.get('lastname')
    mobile = data.get('mobile')

    # Check if all required fields are present
    if not all([email, password, firstname, lastname, mobile]):
        return Response({'success': False, 'message': 'Missing input'}, status=status.HTTP_400_BAD_REQUEST)

    # Check if user already exists
    if UserServices().get_user({'email': email})['success']:
        return Response({'success': False, 'message': 'User already exists'}, status=status.HTTP_400_BAD_REQUEST)

    # Generate a token and tokenize email
    token = get_random_string(length=8)
    tokenized_email = f'{base64.b64encode(email.encode()).decode()}@{token}'

    # Create a temporary user
    temp_user = UserServices().create_user(
        {
            'email': tokenized_email,
            'password': make_password(password),
            'firstname': firstname,
            'lastname': lastname,
            'avatar': '',
            'mobile': mobile,
            'role': '1998',
            'cart': [],
            'address': '',
            'wishlist': [],
            'additionalAddress': [],
            'isBlocked': False,
            'createdAt': datetime.now(),
            'updatedAt': datetime.now(),
        }
    )

    # Send an email
    if temp_user['success']:
        html_content = f'''
        <html>
            <body>
                <p>Dear User,</p>
                <p>Thank you for registering on <strong>Digital World</strong>. To complete your registration process, please use the following verification code:</p>
                <h2>Verification Code:</h2>
                <blockquote><strong>{token}</strong></blockquote>
                <p>Please enter this code on the registration page to verify your account.</p>
                <p>If you did not request this registration, please ignore this email.</p>
                <p>Best regards,<br>
                The Digital World Team</p>
            </body>
        </html>
        '''
        send_email(
            subject='Completing register process!',
            html_message=html_content,
            recipients=[email],
        )
    else:
        return Response({'success': False, 'message': 'An error occurred while creating the user.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    # Schedule deletion of the temporary user
    thread = threading.Thread(
        target=delete_temp_user, args=(tokenized_email,))
    thread.start()

    return Response({'success': True, 'message': 'Temporary user created. Check your email for further instructions.'}, status=status.HTTP_201_CREATED)


# Complete user registration
@api_view(['PUT'])
def complete_register(request, token):
    temp_user = UserServices(
    ).get_temp_user(token)

    if temp_user['success']:
        tokenized_email = temp_user['data']['email']
        email = base64.b64decode(
            tokenized_email.split('@')[0].encode()).decode()

        result = UserServices().update_user(
            {'email': tokenized_email}, {'email': email, })

        if result['success']:
            return Response({'success': True, 'message': 'User registration completed.'})
        else:
            return Response({'success': False, 'message': 'An error occurred while completing the user registration.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# Login a user
@api_view(['POST'])
def login(request):
    # Extract email and password from request data
    email = request.data.get('email')
    password = request.data.get(
        'password')

    # Validate input fields
    if not email or not password:
        return Response({'success': False, 'message': 'Missing input'}, status=status.HTTP_400_BAD_REQUEST)

    # Get the user
    user = UserServices().get_user(
        {'email': email})

    if not user['success']:
        return Response({'success': False, 'message': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

    user_data = user['data']
    hashed_password = user_data.pop(
        'password', None)
    role = user_data.pop('role', None)
    user_data.pop('refreshToken', None)

    # Check if the provided password matches the stored hash
    if not check_password(password, hashed_password):
        return Response({'success': False, 'message': 'Invalid email or password'}, status=status.HTTP_401_UNAUTHORIZED)

    # Generate tokens
    access_token = generate_access_token(
        str(user_data['_id']), role)
    refresh_token = generate_refresh_token(
        str(user_data['_id']))

    # Update user's refresh token in the database
    updated_user = UserServices().update_user(
        {'email': email}, {'refreshToken': refresh_token})

    if not updated_user['success']:
        return Response({'success': False, 'message': 'An error occurred while logging in.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    # Prepare and return response with access token and user data
    response = Response({
        'success': True,
        'accessToken': access_token,
        'userData': convert_to_json_compatible(user_data)
    }, status=status.HTTP_200_OK)

    # Set the refresh token in a secure, HTTP-only cookie
    response.set_cookie(
        key='refreshToken',
        value=refresh_token,
        httponly=True,
        max_age=7*24*60*60
    )

    return response


# Get current user
@api_view(['GET'])
@verify_access_token
def get_current(request):
    _id = request.user['_id']

    user = UserServices().get_current_user(_id)

    if not user['success']:
        return Response({'success': False, 'message': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

    return Response({'success': True, 'rs': convert_to_json_compatible(user['data'])}, status=status.HTTP_200_OK)


# Refresh access token
@api_view(['POST'])
def refresh_access_token(request):
    refresh_token = request.COOKIES.get(
        'refreshToken')

    if not refresh_token:
        return Response({'success': False, 'message': 'No refresh token in cookie'}, status=status.HTTP_401_UNAUTHORIZED)

    # Decode the token
    try:
        decoded_data = jwt.decode(
            refresh_token, settings.SECRET_KEY, algorithms=['HS256'])

        user = UserServices().get_user(
            {'_id': ObjectId(decoded_data['_id']), 'refreshToken': refresh_token})

        if user['success']:
            new_access_token = generate_access_token(
                str(user['data']['_id']), str(user['data']['role']))

            return Response({'success': True, 'newAccessToken': new_access_token}, status=status.HTTP_200_OK)

        return Response({'success': False, 'newAccessToken': 'Invalid or expired token. Please login again!'}, status=status.HTTP_404_NOT_FOUND)

    except (jwt.DecodeError, jwt.ExpiredSignatureError):
        return Response({'success': False, 'message': 'Invalid or expired token'}, status=status.HTTP_401_UNAUTHORIZED)


# Logout a user
@api_view(['GET'])
def logout(request):
    refresh_token = request.COOKIES.get(
        'refreshToken')

    if not refresh_token:
        return Response({'success': False, 'message': 'No refresh token in cookie'}, status=status.HTTP_401_UNAUTHORIZED)

    # Delete refresh token from database
    UserServices().update_user(
        {'refreshToken': refresh_token}, {'refreshToken': ''})

    # Delete refresh token from cookie
    response = Response(
        {'success': True, 'message': 'Logout successfully'}, status=status.HTTP_200_OK)
    response.delete_cookie(
        'refreshToken')

    return response

# forgot password - send email


@api_view(['POST'])
def forgot_password(request):
    email = request.data.get('email')

    if not email:
        return Response({'success': False, 'message': 'Please provide email'}, status=status.HTTP_400_BAD_REQUEST)

    user = UserServices().get_user(
        {'email': email})

    if not user['success']:
        return Response({'success': False, 'message': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

    # Generate a token
    token = generate_password_reset_token(
        str(email))

    html = f'''<html>
                    <body>
                        <p>Dear User,</p>
                        <p>We received a request to reset the password for your account. If you did not make this request, please ignore this email. Otherwise, click the link below within 15 minutes to reset your password:</p>
                        <a href={settings.CLIENT_URL}/resetpassword/{token}>Click here</a>
                        <blockquote><strong>{token}</strong></blockquote>
                        <p>If you did not request this registration, please ignore this email.</p>
                        <p>Best regards,<br>
                        The Digital World Team</p>
                    </body>
                </html>'''

    send_email(
        subject='Forgot password',
        html_message=html,
        recipients=[email]
    )

    return Response({'success': True, 'message': 'Please check your email to reset password!'}, status=status.HTTP_200_OK)


@api_view(['PUT'])
def reset_password(request):
    token = request.data.get('token')
    password = request.data.get(
        'password')

    if not password or not token:
        return Response({'success': False, 'message': 'Please provide password and reset token'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        decoded_data = jwt.decode(
            token, settings.SECRET_KEY, algorithms=['HS256'])
        email = decoded_data['email']

        result = UserServices().update_user(
            {'email': email}, {'password': make_password(password)})

        if result['success']:
            return Response({'success': True, 'message': 'Password reset successfully'}, status=status.HTTP_200_OK)
        else:
            return Response({'success': False, 'message': 'An error occurred while resetting the password'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    except (jwt.DecodeError, jwt.ExpiredSignatureError):
        return Response({'success': False, 'message': 'Invalid or expired token'}, status=status.HTTP_401_UNAUTHORIZED)


# Get all users
@api_view(['GET'])
@verify_access_token
@verify_admin
def get_users(request):
    queries = request.query_params.dict()

    # Separate the specified fields from queries
    excluded_fields = [
        'page', 'sort', 'limit', 'fields']
    queries = {key: value for key,
               value in queries.items() if key not in excluded_fields}

    # Format the queries to be used in mongoodb queries
    formatted_queries = {}
    formatted_queries['find'] = {key.replace(
        '[', '[$') if 'gte' in key or 'gt' in key or 'lt' in key or 'lte' in key else key: value for key, value in queries.items()}

    if queries.get('name'):
        del formatted_queries['find']['name']
        formatted_queries['find']['firstname'] = {
            '$regex': queries['name'], '$options': 'i'}

    if queries.get('q'):
        del formatted_queries['find']['q']
        formatted_queries['find']['$or'] = [
            {'firstname': {
                '$regex': queries['q'], '$options': 'i'}},
            {'lastname': {
                '$regex': queries['q'], '$options': 'i'}},
            {'email': {
                '$regex': queries['q'], '$options': 'i'}},
        ]

    # Sorting
    if request.query_params.get('sort'):
        sort_by = [(e.strip().lstrip('-'), -1 if e.strip().startswith('-') else 1)
                   for e in request.query_params.get('sort').split(',')]
        formatted_queries['sort'] = sort_by

    # Field limiting
    if request.query_params.get('fields'):
        fields = {key.strip(): 1 for key in request.query_params.get(
            'fields').split(',')}
        formatted_queries['fields'] = fields

    # Pagination
    page = int(
        request.query_params.get('page', 1))
    limit = int(
        request.query_params.get('limit', 10))
    skip = (page - 1) * limit
    formatted_queries['skip'] = skip
    formatted_queries['limit'] = limit

    print(formatted_queries)

    users = UserServices().get_users(
        formatted_queries)

    if not users['success']:
        return Response({'success': False, 'message': f'Cannot get users due to {users["error"]}'}, status=status.HTTP_404_NOT_FOUND)

    return Response({'success': True, 'count': len(users['data']), 'users': convert_to_json_compatible(users['data'])}, status=status.HTTP_200_OK)


# Delete a user
@api_view(['DELETE'])
@verify_access_token
@verify_admin
def delete_user(request, user_id):
    if request.user['_id'] == user_id:
        return Response({'success': False, 'message': 'You cannot delete the administrator account that is currently logged in'}, status=status.HTTP_403_FORBIDDEN)
    else:
        result = UserServices().delete_user(
            {'_id': ObjectId(user_id)})

        if not result['success']:
            return Response({'success': False, 'message': 'Cannot delete user'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response({'success': True, 'message': f'User with id {user_id} had been deleted'}, status=status.HTTP_200_OK)


# Update a user
@api_view(['PUT'])
@verify_access_token
def update_user(request):
    data = request.data
    avatar = request.FILES.get('avatar')

    # Check if at least one field is provided
    if not data and not avatar:
        return Response({'success': False, 'message': 'Missing input'}, status=status.HTTP_400_BAD_REQUEST)

    # Check if avatar is provided
    if avatar:
        upload_result = upload_single_image(
            avatar)
        if not upload_result['success']:
            return Response({'success': False, 'message': upload_result['error']}, status=status.HTTP_400_BAD_REQUEST)
        data['avatar'] = upload_result['data']

    # Update user
    result = UserServices().update_user(
        {'_id': ObjectId(request.user['_id'])}, data.dict())

    if not result['success']:
        return Response({'success': False, 'message': result['error']}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    return Response({'success': True, 'message': 'User updated successfully'}, status=status.HTTP_200_OK)


# Update user by admin
@api_view(['PUT'])
@verify_access_token
@verify_admin
def update_user_by_admin(request, user_id):
    data = request.data

    if request.user['_id'] == user_id:
        return Response({'success': False, 'message': 'You cannot delete the administrator account that is currently logged in'}, status=status.HTTP_403_FORBIDDEN)

    # Check if at least one field is provided
    if not data:
        return Response({'success': False, 'message': 'Missing input'}, status=status.HTTP_400_BAD_REQUEST)

    # Update user
    result = UserServices().update_user(
        {'_id': ObjectId(user_id)}, data.dict())

    if not result['success']:
        return Response({'success': False, 'message': result['error']}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    return Response({'success': True, 'message': 'User updated successfully'}, status=status.HTTP_200_OK)


# Update user address
@api_view(['PUT'])
@verify_access_token
def update_user_address(request):
    address = request.data.get(
        'address')

    if not address:
        return Response({'success': False, 'message': 'Missing input'}, status=status.HTTP_400_BAD_REQUEST)

    result = UserServices().update_user_address(
        {'_id': ObjectId(request.user['_id'])}, {'address': address})

    if not result['success']:
        return Response({'success': False, 'message': result['error']}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    return Response({'success': True, 'message': 'User address updated successfully'}, status=status.HTTP_200_OK)


# Update user additional address
@api_view(['PUT'])
@verify_access_token
def update_user_additional_address(request):
    user_id = request.user['_id']
    data = request.data

    if not data['name'] or not data['mobileNo'] or not data['houseNo'] or not data['landmark'] or not data['street'] or not data['city'] or not data['country'] or not data['postalCode']:
        return Response({'success': False, 'message': 'Missing input'}, status=status.HTTP_400_BAD_REQUEST)

    user_additional_address = UserServices().get_user(
        {'_id': ObjectId(user_id)})['data']['additionalAddress']

    is_in_additional_address = next(
        (item for item in user_additional_address if item['name'] == data['name'] and item['mobileNo'] == data['mobileNo'] and item['houseNo'] == data['houseNo'] and item['landmark'] == data['landmark']), None)

    if is_in_additional_address:
        return Response({'success': False, 'message': 'Address already exists'}, status=status.HTTP_400_BAD_REQUEST)
    else:
        response = UserServices().update_user_additional_address(
            'ADD',
            {'_id': ObjectId(user_id)},
            {
                '_id': ObjectId(),
                'name': data['name'],
                'mobileNo': data['mobileNo'],
                'houseNo': data['houseNo'],
                'landmark': data['landmark'],
                'street': data['street'],
                'city': data['city'],
                'country': data['country'],
                'postalCode': data['postalCode'],
            }
        )
        if not response['success']:
            return Response({'success': False, 'message': response['error']}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    print(user_additional_address)

    return Response({'success': True, 'message': 'User additional address updated successfully'}, status=status.HTTP_200_OK)


# Remove user additional address
@api_view(['DELETE'])
@verify_access_token
def remove_user_additional_address(request, address_id):
    user_id = request.user['_id']

    user_additional_address = UserServices().get_user(
        {'_id': ObjectId(user_id)})['data']['additionalAddress']

    is_in_additional_address = next(
        (item for item in user_additional_address if str(item['_id']) == address_id), None)

    if not is_in_additional_address:
        return Response({'success': False, 'message': 'Address not found'}, status=status.HTTP_404_NOT_FOUND)
    else:
        response = UserServices().update_user_additional_address(
            'REMOVE',
            {'_id': ObjectId(user_id)},
            {'_id': ObjectId(address_id)}
        )
        if not response['success']:
            return Response({'success': False, 'message': response['error']}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    return Response({'success': True, 'message': 'User additional address removed successfully'}, status=status.HTTP_200_OK)


# Update user cart
@api_view(['PUT'])
@verify_access_token
def update_user_cart(request):
    user_id = request.user['_id']
    data = request.data

    if not data['pid'] or not data['color']:
        return Response({'success': False, 'message': 'Missing input'}, status=status.HTTP_400_BAD_REQUEST)

    user_cart = UserServices().get_user(
        {'_id': ObjectId(user_id)})['data']['cart']

    already_added_item = next(
        (item for item in user_cart if str(item['product']) == data['pid'] and item['color'].upper() == data['color'].upper()), None)

    if already_added_item:
        response = UserServices().update_user_cart(
            'IS_EXISTED',
            {'_id': ObjectId(user_id), 'cart.product': already_added_item['product'],
                'cart.color': already_added_item['color']},
            int(data.get('quantity', 1)),
        )
        if not response['success']:
            return Response({'success': False, 'message': response['error']}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    else:
        response = UserServices().update_user_cart(
            'IS_NOT_EXISTED',
            {'_id': ObjectId(user_id)},
            {
                'product': ObjectId(data['pid']),
                'quantity': int(data.get('quantity', 1)),
                'color': data['color'],
                'thumnail': data['thumbnail'],
                'title': data['title'],
                'price': float(data['price']),
                '_id': ObjectId()
            }
        )
        if not response['success']:
            return Response({'success': False, 'message': response['error']}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    return Response({'success': True, 'message': 'User cart updated successfully'}, status=status.HTTP_200_OK)


# Remove product from user cart
@api_view(['DELETE'])
@verify_access_token
def remove_from_cart(request, pid, color):
    user_id = request.user['_id']

    if not pid or not color:
        return Response({'success': False, 'message': 'Missing input'}, status=status.HTTP_400_BAD_REQUEST)

    user_cart = UserServices().get_user(
        {'_id': ObjectId(user_id)})['data']['cart']

    already_added_item = next(
        (item for item in user_cart if str(item['product']) == pid and item['color'].upper() == color.upper()), None)

    if not already_added_item:
        return Response({'success': False, 'message': 'Item has not been in cart'}, status=status.HTTP_200_OK)
    else:
        response = UserServices().update_user_cart(
            'REMOVE',
            {'_id': ObjectId(user_id), 'cart.product': already_added_item['product'],
                'cart.color': already_added_item['color']},
            {'product': already_added_item['product'],
             'color': already_added_item['color']},
        )
        if not response['success']:
            return Response({'success': False, 'message': response['error']}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    return Response({'success': True, 'message': 'Item removed from cart successfully'}, status=status.HTTP_200_OK)


# Update user wishlist
@api_view(['PUT'])
@verify_access_token
def update_user_wishlist(request, pid):
    user_id = request.user['_id']

    if not pid:
        return Response({'success': False, 'message': 'Missing input'}, status=status.HTTP_400_BAD_REQUEST)

    user_wishlist = UserServices().get_user(
        {'_id': ObjectId(user_id)})['data']['wishlist']

    is_in_wishlist = next(
        (item for item in user_wishlist if str(item) == pid), None)

    if is_in_wishlist:
        response = UserServices().update_user_wishlist(
            'REMOVE',
            {'_id': ObjectId(user_id)},
            ObjectId(pid)
        )
        if not response['success']:
            return Response({'success': False, 'message': response['error']}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    else:
        response = UserServices().update_user_wishlist(
            'ADD',
            {'_id': ObjectId(user_id)},
            ObjectId(pid)
        )
        if not response['success']:
            return Response({'success': False, 'message': response['error']}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    return Response({'success': True, 'message': 'User wishlist had been updated successfully'}, status=status.HTTP_200_OK)
