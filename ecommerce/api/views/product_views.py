from api.services.product_services import ProductServices
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from api.common.utils import convert_to_json_compatible, upload_single_image, upload_multiple_images, unique_slugify, generate_sku
from api.common.decorators import verify_access_token, verify_admin
from bson import ObjectId
from datetime import datetime
import re


# CreateCreate a new product
@api_view(["POST"])
@verify_access_token
@verify_admin
def create_product(request):
    data = request.data
    thumb = request.FILES.get('thumb')
    images = request.FILES.getlist('images')

    if not data['title'] or not data['description'] or not data['price'] or not data['category'] or not data['brand'] or not data['color'] or not thumb or not images:
        return Response({"success": False, "message": "Missing inputs"}, status=status.HTTP_400_BAD_REQUEST)

    # upload thumb
    thumb_upload_result = upload_single_image(thumb)
    if not thumb_upload_result['success']:
        return Response({'success': False, 'message': f'Cannot create product due to {thumb_upload_result["error"]}'}, status=status.HTTP_400_BAD_REQUEST)
    data['thumb'] = thumb_upload_result['data']

    # upload images
    images_upload_result = upload_multiple_images(images)
    if not images_upload_result['success']:
        return Response({'success': False, 'message': f'Cannot create product due to {images_upload_result["error"]}'}, status=status.HTTP_400_BAD_REQUEST)
    data['images'] = images_upload_result['data']

    # create product
    response = ProductServices().create_product({
        'title': data['title'],
        'description': [data['description']],
        'price': float(data['price']),
        'category': data['category'],
        'brand': data['brand'],
        'color': data['color'],
        'thumb': data['thumb'],
        'images': data['images'],
        'slug': unique_slugify(data['title']),
        'quantity': int(data.get('quantity', 0)),
        'ratings': [],
        'variant': [],
        'sold': 0,
        'totalRating': 0,
        'createdAt': datetime.now(),
        'updatedAt': datetime.now()
    })
    if not response['success']:
        return Response({"success": False, "message": response['error']}, status=status.HTTP_400_BAD_REQUEST)

    return Response({"success": True, "message": "Product created successfully"}, status=status.HTTP_201_CREATED)


# Get all products
@api_view(['GET'])
def get_products(request):
    queries = request.query_params.dict()

    # Separate the specified fields from queries
    excluded_fields = [
        'page', 'sort', 'limit', 'fields']
    queries = {key: value for key,
               value in queries.items() if key not in excluded_fields}

    # Format the queries to be used in mongoodb queries
    formatted_queries = {}
    formatted_queries['no_q'] = {}
    formatted_queries['q'] = {}
    formatted_queries['find'] = {}
    formatted_queries['query_list'] = []

    # If there is a price query, convert it to a appropriate dictionary
    price_key = [key for key in queries if 'price[' in key]
    if price_key:
        match = re.match(r'([a-zA-Z0-9]+)\[(\w+)\]', str(price_key[0]))
        if match:
            field, operator = match.groups()
            formatted_queries['no_q'][field] = {
                f'${operator}': float(queries.pop(price_key[0]))}
    elif queries.get('price'):
        formatted_queries['no_q']['price'] = float(queries.get('price'))

    if queries.get('title'):
        formatted_queries['no_q']['title'] = {
            '$regex': queries['title'], '$options': 'i'}

    if queries.get('category'):
        formatted_queries['no_q']['category'] = {
            '$regex': queries['category'], '$options': 'i'}

    if queries.get('brand'):
        formatted_queries['no_q']['brand'] = {
            '$regex': queries['brand'], '$options': 'i'}

    if queries.get('color'):
        color_list = queries['color'].split(',')
        color_query = [{'color': {'$regex': color.strip(), '$options': 'i'}}
                       for color in color_list]
        formatted_queries['no_q']['$or'] = color_query

    if queries.get('q'):
        formatted_queries['q']['$or'] = [
            {'title': {
                '$regex': queries['q'], '$options': 'i'}},
            {'category': {
                '$regex': queries['q'], '$options': 'i'}},
            {'brand': {
                '$regex': queries['q'], '$options': 'i'}},
        ]

    if formatted_queries['q']:
        formatted_queries['query_list'].append(formatted_queries['no_q'])
        formatted_queries['query_list'].append(formatted_queries['q'])
    else:
        formatted_queries['query_list'].append(formatted_queries['no_q'])

    del formatted_queries['no_q']
    del formatted_queries['q']

    formatted_queries['find'] = {'$and': formatted_queries['query_list']}
    del formatted_queries['query_list']

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

    response = ProductServices().get_products(
        formatted_queries)

    if not response['success']:
        return Response({'success': False, 'message': f'Cannot get products due to {response["error"]}'}, status=status.HTTP_404_NOT_FOUND)

    return Response({'success': True, 'count': len(response['data']), 'products': convert_to_json_compatible(response['data'])}, status=status.HTTP_200_OK)


# Get a single product
@api_view(['GET'])
def get_product(request, pid):

    if not pid:
        return Response({'success': False, 'message': 'Product id is required'}, status=status.HTTP_400_BAD_REQUEST)

    response = ProductServices().get_product(pid)

    if not response['success']:
        return Response({'success': False, 'message': f'Cannot get product due to {response["error"]}'}, status=status.HTTP_404_NOT_FOUND)

    return Response({'success': True, 'product': convert_to_json_compatible(response['data'])}, status=status.HTTP_200_OK)


# Update a product
@api_view(['PUT'])
@verify_access_token
@verify_admin
def update_product(request, pid):
    data = request.data.dict()

    if not pid:
        return Response({'success': False, 'message': 'Product id is required'}, status=status.HTTP_400_BAD_REQUEST)

    if not data:
        return Response({'success': False, 'message': 'No data to update'}, status=status.HTTP_400_BAD_REQUEST)

    # Check if the product exists
    product = ProductServices().get_product(pid)
    if not product['success']:
        return Response({'success': False, 'message': f'There is no product to update'}, status=status.HTTP_404_NOT_FOUND)

    if data.get('title'):
        data['slug'] = unique_slugify(data['title'])

    if data.get('price'):
        data['price'] = float(data['price'])

    if data.get('quantity'):
        data['quantity'] = int(data['quantity'])

    if data.get('thumb'):
        thumb = request.FILES.get('thumb')
        thumb_upload_result = upload_single_image(thumb)
        if not thumb_upload_result['success']:
            return Response({'success': False, 'message': f'Cannot update product due to {thumb_upload_result["error"]}'}, status=status.HTTP_400_BAD_REQUEST)
        data['thumb'] = thumb_upload_result['data']

    if data.get('images'):
        images = request.FILES.getlist('images')
        images_upload_result = upload_multiple_images(images)
        if not images_upload_result['success']:
            return Response({'success': False, 'message': f'Cannot update product due to {images_upload_result["error"]}'}, status=status.HTTP_400_BAD_REQUEST)
        data['images'] = images_upload_result['data']

    response = ProductServices().update_product({'_id': ObjectId(pid)}, data)
    if not response['success']:
        return Response({'success': False, 'message': f'Cannot update product due to {response["error"]}'}, status=status.HTTP_400_BAD_REQUEST)

    return Response({'success': True, 'message': 'Product has been updated successfully'}, status=status.HTTP_200_OK)


# Delete a product
@api_view(['DELETE'])
@verify_access_token
@verify_admin
def delete_product(request, pid):
    if not pid:
        return Response({'success': False, 'message': 'Product id is required'}, status=status.HTTP_400_BAD_REQUEST)

    response = ProductServices().delete_product({'_id': ObjectId(pid)})
    if not response['success']:
        return Response({'success': False, 'message': f'Cannot delete product due to {response["error"]}'}, status=status.HTTP_400_BAD_REQUEST)

    return Response({'success': True, 'message': 'Product has been deleted successfully'}, status=status.HTTP_200_OK)


# Update product ratings
@api_view(['PUT'])
@verify_access_token
def update_ratings(request):
    user_id = request.user['_id']
    data = request.data.dict()

    # Check if the required fields are present
    if not data.get('pid') or not data.get('star') or not data.get('comment'):
        return Response({'success': False, 'message': 'Missing inputs'}, status=status.HTTP_400_BAD_REQUEST)

    # Get the product ratings
    ratings = ProductServices().get_product(data['pid'])[
        'data'].get('ratings', [])

    data['updatedAt'] = datetime.now()

    # Check if the user has already rated the product
    already_rated = [rating for rating in ratings if str(
        rating['postedBy']) == user_id]

    if already_rated:
        response = ProductServices().update_ratings(
            {'_id': ObjectId(data['pid']), 'ratings.postedBy': ObjectId(user_id)}, 'MODIFY', data)
        if not response['success']:
            return Response({'success': False, 'message': f'Cannot update rating due to {response["error"]}'}, status=status.HTTP_400_BAD_REQUEST)
    else:
        response = ProductServices().update_ratings(
            {'_id': ObjectId(data['pid'])}, 'ADD', {'star': int(data['star']), 'comment': data['comment'], 'postedBy': ObjectId(user_id), 'updatedAt': data['updatedAt'], '_id': ObjectId()})
        if not response['success']:
            return Response({'success': False, 'message': f'Cannot update rating due to {response["error"]}'}, status=status.HTTP_400_BAD_REQUEST)

    # Update the total rating
    ratings = ProductServices().get_product(data['pid'])[
        'data'].get('ratings', [])
    total_rating = sum([rating['star'] for rating in ratings])
    response = ProductServices().update_product({'_id': ObjectId(data['pid'])}, {
        'totalRating': round(total_rating/len(ratings), 1)})
    if not response['success']:
        return Response({'success': False, 'message': f'Cannot update rating due to {response["error"]}'}, status=status.HTTP_400_BAD_REQUEST)

    return Response({'success': True, 'message': 'Rating has been updated successfully'}, status=status.HTTP_200_OK)


# Upload product images
@api_view(['PUT'])
@verify_access_token
@verify_admin
def upload_images(request, pid):
    if not pid:
        return Response({'success': False, 'message': 'Product id is required'}, status=status.HTTP_400_BAD_REQUEST)

    images = request.FILES.getlist('images')

    if not images:
        return Response({'success': False, 'message': 'No images to upload'}, status=status.HTTP_400_BAD_REQUEST)

    images_upload_result = upload_multiple_images(images)
    if not images_upload_result['success']:
        return Response({'success': False, 'message': f'Cannot upload images due to {images_upload_result["error"]}'}, status=status.HTTP_400_BAD_REQUEST)

    response = ProductServices().upload_images(
        {'_id': ObjectId(pid)}, images_upload_result['data'])
    if not response['success']:
        return Response({'success': False, 'message': f'Cannot upload images due to {response["error"]}'}, status=status.HTTP_400_BAD_REQUEST)

    return Response({'success': True, 'message': 'Product images have been uploaded'}, status=status.HTTP_200_OK)


# Add a variant to a product
@api_view(['PUT'])
@verify_access_token
@verify_admin
def add_variant(request, pid):
    data = request.data

    if not pid or not data.get('title') or not data.get('price') or not data.get('price') or not data.get('color') or not data.get('thumb') or not data.get('images'):
        return Response({'success': False, 'message': 'Missing inputs'}, status=status.HTTP_400_BAD_REQUEST)

    data = data.dict()

    # Upload thumb
    thumb_upload_result = upload_single_image(request.FILES.get('thumb'))
    if not thumb_upload_result['success']:
        return Response({'success': False, 'message': f'Cannot add variant due to {thumb_upload_result["error"]}'}, status=status.HTTP_400_BAD_REQUEST)
    data['thumb'] = thumb_upload_result['data']

    # Upload images
    images_upload_result = upload_multiple_images(
        request.FILES.getlist('images'))
    if not images_upload_result['success']:
        return Response({'success': False, 'message': f'Cannot add variant due to {images_upload_result["error"]}'}, status=status.HTTP_400_BAD_REQUEST)
    data['images'] = images_upload_result['data']

    print(data)

    response = ProductServices().add_variant({'_id': ObjectId(pid)}, {'title': data['title'], 'price': float(
        data['price']), 'color': data['color'], 'thumb': data['thumb'], 'images': data['images'], 'sku': generate_sku(), '_id': ObjectId()})
    if not response['success']:
        return Response({'success': False, 'message': f'Cannot add variant due to {response["error"]}'}, status=status.HTTP_400_BAD_REQUEST)

    return Response({'success': True, 'message': 'A new variant has been added'}, status=status.HTTP_200_OK)
