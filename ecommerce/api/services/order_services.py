from django.conf import settings
from pymongo.errors import PyMongoError
from bson import ObjectId


class OrderServices:
    def __init__(self):
        self.order_collection = settings.DB["orders"]

    # Create a new order
    def create_order(self, order_data):
        try:
            result = self.order_collection.insert_one(order_data)
            if result.inserted_id is not None:
                return {'success': True, 'data': str(result.inserted_id)}
            else:
                return {'success': False, 'error': 'An error occurred while creating the order.'}
        except PyMongoError as e:
            return {'success': False, 'error': f'An error occurred while creating the order: {e}'}
        except Exception as e:
            return {'success': False, 'error': f'An unexpected error occurred: {e}'}

    # Update order status
    def update_order(self, upadate_by, data):
        try:
            result = self.order_collection.update_one(
                upadate_by, {'$set': data})
            if result.modified_count > 0:
                return {'success': True, 'message': 'Order status updated successfully.'}
            else:
                return {'success': False, 'error': 'An error occurred while updating the order status.'}
        except PyMongoError as e:
            return {'success': False, 'error': f'An error occurred while updating the order status: {e}'}
        except Exception as e:
            return {'success': False, 'error': f'An unexpected error occurred: {e}'}

    # Get all orders
    def get_orders(self, query_data):
        try:
            result = None
            if 'fields' not in query_data and 'sort' not in query_data:
                result = list(self.order_collection.find(query_data['find']).skip(
                    query_data['skip']).limit(query_data['limit']))
            elif 'sort' not in query_data:
                result = list(self.order_collection.find(query_data['find'], query_data['fields']).skip(
                    query_data['skip']).limit(query_data['limit']))
            elif 'fields' not in query_data:
                result = list(self.order_collection.find(query_data['find']).sort(
                    query_data['sort']).skip(query_data['skip']).limit(query_data['limit']))
            else:
                result = list(self.order_collection.find(query_data['find'], query_data['fields']).sort(
                    query_data['sort']).skip(query_data['skip']).limit(query_data['limit']))
            if result is None:
                return {'success': False, 'error': f'No order found with the given query data.'}
            else:
                return {'success': True, 'data': result}
        except PyMongoError as e:
            return {'success': False, 'error': f'An error occurred while getting the orders: {e}'}
        except Exception as e:
            return {'success': False, 'error': f'An unexpected error occurred: {e}'}
