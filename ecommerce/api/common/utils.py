from bson import ObjectId
from datetime import datetime, timezone
from django.core.mail import send_mail
from django.conf import settings
import jwt
from datetime import datetime, timedelta
from cloudinary.uploader import upload
from cloudinary.exceptions import Error
from django.utils.text import slugify
import uuid

# Convert a MongoDB document to a JSON-compatible format


def convert_to_json_compatible(obj):
    if isinstance(obj, dict):
        return {key: convert_to_json_compatible(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [convert_to_json_compatible(item) for item in obj]
    elif isinstance(obj, ObjectId):
        return str(obj)
    elif isinstance(obj, datetime):
        return obj.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
    else:
        return obj


# Send an email
def send_email(subject='', message='', html_message='', recipients=[]):
    send_mail(
        subject=subject,
        message=message,
        html_message=html_message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=recipients,
    )


# Generate access token
def generate_access_token(_id, role):
    payload = {
        "_id": _id,
        "role": role,
        "exp": datetime.now(timezone.utc) + timedelta(hours=24),
        "iat": datetime.now(timezone.utc)
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm='HS256')


# Generate refresh token
def generate_refresh_token(_id):
    payload = {
        "_id": _id,
        "exp": datetime.now(timezone.utc) + timedelta(days=7),
        "iat": datetime.now(timezone.utc)
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm='HS256')


# Generate password reset token
def generate_password_reset_token(email):
    payload = {
        "email": email,
        "exp": datetime.now(timezone.utc) + timedelta(minutes=15),
        "iat": datetime.now(timezone.utc)
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm='HS256')


# Validate image before uploading to Cloudinary
def Validate_image(file, allowed_formats=['image/jpg', 'image/jpeg', 'image/png'], max_size=2):
    if file.size > max_size * 1024 * 1024:
        return {'success': False, 'error': f'Image size should be less than {max_size}MB.'}
    if file.content_type not in allowed_formats:
        return {'success': False, 'error': f'Image format not supported. Use {", ".join(allowed_formats)}.'}
    return {'success': True, 'message': 'Image is valid.'}


# Upload single image to Cloudinary
def upload_single_image(file, transformation=None):
    if Validate_image(file)['success'] is False:
        return {'success': False, 'error': Validate_image(file)['error']}

    try:
        response = upload(file, folder='digitalshop',
                          transformation=transformation or {})
        return {'success': True, 'data': response['secure_url']}
    except Error as e:
        return {'success': False, 'error': f'An error occurred while uploading the image: {e}'}


# Upload multiple images to Cloudinary
def upload_multiple_images(files, transformation=None):
    urls = []
    for file in files:
        if Validate_image(file)['success'] is False:
            continue
        try:
            response = upload(file, folder='digitalshop',
                              transformation=transformation or {})
            urls.append(response['secure_url'])
        except Error as e:
            return {'success': False, 'error': f'An error occurred while uploading the image: {e}'}
    return {'success': True, 'data': urls}


# Generate a unique slug
def unique_slugify(title):
    slug = slugify(title)
    unique_slug = f"{slug}-{uuid.uuid4().hex[:8]}"
    return unique_slug


# Generate a unique SKU
def generate_sku():
    return "SKU" + str(uuid.uuid4().hex[:13]).upper()
