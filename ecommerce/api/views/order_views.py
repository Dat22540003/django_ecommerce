from api.services.order_services import OrderServices
from api.services.user_services import UserServices
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from api.common.utils import convert_to_json_compatible
from api.common.decorators import verify_access_token, verify_admin
from bson import ObjectId
from datetime import datetime
import re


# Create a new order
@api_view(['POST'])
@verify_access_token
def create_order(request):
    user_id = request.user["_id"]
    data = request.data

    # Get user cart and check if it is empty
    user_cart = UserServices().get_user(
        {'_id': ObjectId(user_id)})['data']['cart']

    if not user_cart:
        return Response({'success': False, 'message': 'Your cart is empty!'}, status=status.HTTP_400_BAD_REQUEST)

    # Calculate total price of the order
    total = sum([product['price'] * product['quantity']
                for product in user_cart])

    # Update user address if it is provided
    if data.get('address'):
        response = UserServices().update_user_address(
            {'_id': ObjectId(request.user['_id'])}, {'address': data['address']})
        if not response:
            return Response({'success': False, 'message': 'Cannot create order because of the update of address was fail'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    # Prepare order data
    order_data = {
        '_id': ObjectId(),
        'products': user_cart,
        'total': total,
        'orderBy': ObjectId(user_id),
        'status': data.get('status', 'Succeed'),
        'createdAt': datetime.now(),
        'updatedAt': datetime.now()
    }

    # Create order
    response = OrderServices().create_order(order_data)
    if not response['success']:
        return Response({'success': False, 'message': f'Cannot create order due to {response["error"]}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    # Clear user cart
    UserServices().update_user_cart(
        'CLEAR', {'_id': ObjectId(user_id)},  [])

    return Response({'success': True, 'message': 'Order created successfully'}, status=status.HTTP_201_CREATED)


# Update order status
@api_view(['PUT'])
@verify_access_token
@verify_admin
def update_order_status(request, order_id):
    data = request.data

    if not data.get('status'):
        return Response({'success': False, 'message': 'Status is required'}, status=status.HTTP_400_BAD_REQUEST)

    # Update order status
    response = OrderServices().update_order(
        {'_id': ObjectId(order_id)}, {'status': data['status']})
    if not response['success']:
        return Response({'success': False, 'message': f'Cannot update order status due to {response["error"]}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    return Response({'success': True, 'message': 'Order status updated successfully'}, status=status.HTTP_200_OK)


# Get all orders
@api_view(['GET'])
@verify_access_token
@verify_admin
def get_all_orders(request):
    queries = request.query_params.dict()

    # Separate the specified fields from queries
    excluded_fields = [
        'page', 'sort', 'limit', 'fields']
    queries = {key: value for key,
               value in queries.items() if key not in excluded_fields}

    formatted_queries = {}
    formatted_queries['find'] = {}

    # If there is a price query, convert it to a appropriate dictionary
    total_key = [key for key in queries if 'total[' in key]
    if total_key:
        match = re.match(r'([a-zA-Z0-9]+)\[(\w+)\]', str(total_key[0]))
        if match:
            field, operator = match.groups()
            formatted_queries['find'][field] = {
                f'${operator}': float(queries.pop(total_key[0]))}
    elif queries.get('total'):
        formatted_queries['find']['total'] = float(queries.get('total'))

    # If there is a status query, convert it to a appropriate dictionary
    if queries.get('status'):
        formatted_queries['find']['status'] = {
            '$regex': queries['status'], '$options': 'i'}

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

    response = OrderServices().get_orders(
        formatted_queries)

    if not response['success']:
        return Response({'success': False, 'message': f'Cannot get orders due to {response["error"]}'}, status=status.HTTP_404_NOT_FOUND)

    return Response({'success': True, 'count': len(response['data']), 'orders': convert_to_json_compatible(response['data'])}, status=status.HTTP_200_OK)


@api_view(['GET'])
@verify_access_token
def get_user_orders(request):
    user_id = request.user["_id"]
    queries = request.query_params.dict()

    # Separate the specified fields from queries
    excluded_fields = [
        'page', 'sort', 'limit', 'fields']
    queries = {key: value for key,
               value in queries.items() if key not in excluded_fields}

    formatted_queries = {}
    formatted_queries['find'] = {'orderBy': ObjectId(user_id)}

    # If there is a price query, convert it to a appropriate dictionary
    total_key = [key for key in queries if 'total[' in key]
    if total_key:
        match = re.match(r'([a-zA-Z0-9]+)\[(\w+)\]', str(total_key[0]))
        if match:
            field, operator = match.groups()
            formatted_queries['find'][field] = {
                f'${operator}': float(queries.pop(total_key[0]))}
    elif queries.get('total'):
        formatted_queries['find']['total'] = float(queries.get('total'))

    # If there is a status query, convert it to a appropriate dictionary
    if queries.get('status'):
        formatted_queries['find']['status'] = {
            '$regex': queries['status'], '$options': 'i'}

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

    response = OrderServices().get_orders(
        formatted_queries)

    if not response['success']:
        return Response({'success': False, 'message': f'Cannot get orders due to {response["error"]}'}, status=status.HTTP_404_NOT_FOUND)

    return Response({'success': True, 'count': len(response['data']), 'orders': convert_to_json_compatible(response['data'])}, status=status.HTTP_200_OK)
