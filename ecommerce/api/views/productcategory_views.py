from api.services.productcategory_services import ProductcategoryServices
from api.services.user_services import UserServices
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from api.common.utils import upload_single_image, convert_to_json_compatible
from api.common.decorators import verify_access_token, verify_admin
from bson import ObjectId
from datetime import datetime
import json


# create a new product category
@api_view(['POST'])
@verify_access_token
@verify_admin
def create_productcategory(request):
    brand = request.POST.get('brand')
    title = request.POST.get('title')
    image = request.FILES.get('image')

    if not title or not brand or not image:
        return Response({'success': False, 'message': 'Missing inputs'}, status=status.HTTP_400_BAD_REQUEST)

    if not title.strip():
        return Response({'success': False, 'message': 'Invalid inputs'}, status=status.HTTP_400_BAD_REQUEST)

    # upload image
    image_upload_result = upload_single_image(image)
    if not image_upload_result['success']:
        return Response({'success': False, 'message': f'Cannot create product due to {image_upload_result["error"]}'}, status=status.HTTP_400_BAD_REQUEST)
    image = image_upload_result['data']

    response = ProductcategoryServices().create_productcategory(
        {'title': title, 'brand': json.loads(brand), 'image': image, 'createdAt': datetime.now(), 'updatedAt': datetime.now()})
    if not response['success']:
        return Response({'success': False, 'message': f'Cannot create product category due to {response["error"]}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    return Response({'success': True, 'message': 'Product category created successfully'}, status=status.HTTP_201_CREATED)


# Get all product categories
@api_view(['GET'])
def get_productcategories(request):
    response = ProductcategoryServices().get_productcategories()
    if not response['success']:
        return Response({'success': False, 'message': f'Cannot get product categories due to {response["error"]}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    return Response({'success': True, 'data': convert_to_json_compatible(response['data'])}, status=status.HTTP_200_OK)


# Update product category
@api_view(['PUT'])
@verify_access_token
@verify_admin
def update_productcategory(request, productcategory_id):
    title = request.data.get('title')
    brand = request.data.get('brand')
    image = request.FILES.get('image')
    updated_data = {}

    if not productcategory_id:
        return Response({'success': False, 'message': 'Missing inputs'}, status=status.HTTP_400_BAD_REQUEST)

    if not title and not brand and not image:
        return Response({'success': False, 'message': 'Missing inputs'}, status=status.HTTP_400_BAD_REQUEST)

    # upload image
    if image:
        image_upload_result = upload_single_image(image)
        if not image_upload_result['success']:
            return Response({'success': False, 'message': f'Cannot update product category due to {image_upload_result["error"]}'}, status=status.HTTP_400_BAD_REQUEST)
        updated_data['image'] = image_upload_result['data']

    if title:
        if not title.strip():
            return Response({'success': False, 'message': 'Invalid inputs'}, status=status.HTTP_400_BAD_REQUEST)
        updated_data['title'] = title

    if brand:
        updated_data['brand'] = json.loads(brand)

    updated_data['updatedAt'] = datetime.now()

    response = ProductcategoryServices().update_productcategory(
        {'_id': ObjectId(productcategory_id)}, updated_data)
    if not response['success']:
        return Response({'success': False, 'message': f'Cannot update product category due to {response["error"]}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    return Response({'success': True, 'message': 'Product category updated successfully'}, status=status.HTTP_200_OK)


# Delete product category
@api_view(['DELETE'])
@verify_access_token
@verify_admin
def delete_productcategory(request, productcategory_id):
    if not productcategory_id:
        return Response({'success': False, 'message': 'Missing inputs'}, status=status.HTTP_400_BAD_REQUEST)

    response = ProductcategoryServices().delete_productcategory(
        {'_id': ObjectId(productcategory_id)})
    if not response['success']:
        return Response({'success': False, 'message': f'Cannot delete product category due to {response["error"]}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    return Response({'success': True, 'message': 'Product category deleted successfully'}, status=status.HTTP_200_OK)
