from django.conf import settings
from pymongo.errors import PyMongoError
from bson import ObjectId


class UserServices:
    def __init__(self):
        self.user_collection = settings.DB['users']

    # Create a user
    def create_user(self, user_data):
        try:
            result = self.user_collection.insert_one(user_data)

            if result.inserted_id is not None:
                return {'success': True, 'data': str(result.inserted_id)}
            else:
                return {'success': False, 'error': 'An error occurred while creating the user.'}

        except PyMongoError as e:
            return f'An error occurred while creating the user: {e}'
        except Exception as e:
            return f'An unexpected error occurred: {e}'

    # Get a user
    def get_user(self, query_data):
        try:
            result = self.user_collection.find_one(
                query_data)

            if result is None:
                return {'success': False, 'error': f'No user found with the given query data.'}
            else:
                return {'success': True, 'data': result}
        except PyMongoError as e:
            return {'success': False, 'error': f'An error occurred while getting the user: {e}'}
        except Exception as e:
            return {'success': False, 'error': f'An unexpected error occurred: {e}'}

    # Get all users
    def get_users(self, query_data):
        try:
            result = list(self.user_collection.find(query_data['find'], query_data['fields']).sort(
                query_data['sort']).skip(query_data['skip']).limit(query_data['limit']))

            print(f'length of results: {len(result)}')

            if result is None:
                return {'success': False, 'error': f'No user found with the given query data.'}
            else:
                return {'success': True, 'data': result}
        except PyMongoError as e:
            return {'success': False, 'error': f'An error occurred while getting the user: {e}'}
        except Exception as e:
            return {'success': False, 'error': f'An unexpected error occurred: {e}'}

    # Get a temporary user
    def get_temp_user(self, token):
        try:
            result = self.user_collection.find_one(
                {'email': {'$regex': f'{token}$'}})

            if result is None:
                return {'success': False, 'error': f'No user found with token {token}'}
            else:
                return {'success': True, 'data': result}
        except PyMongoError as e:
            return {'success': False, 'error': f'An error occurred while getting the user: {e}'}
        except Exception as e:
            return {'success': False, 'error': f'An unexpected error occurred: {e}'}

    # Get current user
    def get_current_user(self, user_id):
        try:
            pipeline = [
                {
                    '$match': {
                        '_id': ObjectId(user_id)
                    }
                },
                {
                    '$lookup': {
                        'from': 'products',
                        'localField': 'wishlist',
                        'foreignField': '_id',
                        'as': 'wishlist',
                    }
                },
                {
                    '$lookup': {
                        'from': 'products',
                        'localField': 'cart.product',
                        'foreignField': '_id',
                        'as': 'cartDetails',
                    },
                },
                {
                    '$project': {
                        'firstname': 1,
                        'lastname': 1,
                        'email': 1,
                        'avatar': 1,
                        'mobile': 1,
                        'role': 1,
                        'address': 1,
                        'isBlocked': 1,
                        'createdAt': 1,
                        'updatedAt': 1,
                        'passwordChangedAt': 1,
                        'passwordResetToken': 1,
                        'passwordResetExpires': 1,
                        'registerToken': 1,
                        'additionalAddress': 1,
                        'wishlist': {
                            '$map': {
                                'input': '$wishlist',
                                'as': 'item',
                                'in': {
                                    '_id': '$$item._id',
                                    'title': '$$item.title',
                                    'thumb': '$$item.thumb',
                                    'price': '$$item.price',
                                    'color': '$$item.color'
                                }
                            }
                        },
                        'cart': {
                            '$map': {
                                'input': '$cart',
                                'as': 'item',
                                'in': {
                                    'quantity': '$$item.quantity',
                                    'color': '$$item.color',
                                    'price': '$$item.price',
                                    'thumbnail': '$$item.thumbnail',
                                    'title': '$$item.title',
                                    '_id': '$$item._id',
                                    'product': {
                                        '$let': {
                                            'vars': {
                                                'productDetails': {
                                                    '$arrayElemAt': [
                                                        '$cartDetails',
                                                        {
                                                            '$indexOfArray': [
                                                                '$cartDetails._id',
                                                                '$$item.product'
                                                            ]
                                                        }
                                                    ],
                                                }
                                            },
                                            'in': {
                                                '_id': '$$productDetails._id',
                                                'title': '$$productDetails.title',
                                                'thumb': '$$productDetails.thumb',
                                                'price': '$$productDetails.price',
                                            }
                                        },

                                    }
                                }
                            }
                        },
                    },
                }
            ]

            # Execute the pipeline
            result = list(self.user_collection.aggregate(pipeline))

            if result is None:
                return {'success': False, 'error': f'No user found with the given ID.'}
            else:
                return {'success': True, 'data': result[0]}
        except PyMongoError as e:
            return {'success': False, 'error': f'An error occurred while getting the user: {e}'}
        except Exception as e:
            return {'success': False, 'error': f'An unexpected error occurred: {e}'}

    # Update a user
    def update_user(self, update_by, user_data):
        try:
            result = self.user_collection.update_one(
                update_by, {'$set': user_data})

            if result.modified_count > 0:
                return {'success': True, 'message': f'User had been updated successfully.'}
            else:
                return {'success': False, 'error': f'No user found or no changes made.'}

        except PyMongoError as e:
            return {'success': False, 'error': f'An error occurred while updating the user: {e}'}
        except Exception as e:
            return {'success': False, 'error': f'An unexpected error occurred: {e}'}

    # Update user address

    def update_user_address(self, update_by, address):
        try:
            result = self.user_collection.update_one(
                update_by, {'$push': address})

            if result.modified_count > 0:
                return {'success': True, 'message': f'User address had been updated successfully.'}
            else:
                return {'success': False, 'error': f'No user found or no changes made.'}

        except PyMongoError as e:
            return {'success': False, 'error': f'An error occurred while updating the user: {e}'}
        except Exception as e:
            return {'success': False, 'error': f'An unexpected error occurred: {e}'}

    # Delete a user
    def delete_user(self, user_info):
        try:
            result = self.user_collection.delete_one(user_info)
            print(f'result: {result}')
            if result.deleted_count > 0:
                return {'success': True, 'message': f'User had been deleted successfully.'}
            else:
                return {'success': False, 'message': f'No user found with the given information.'}

        except PyMongoError as e:
            return {'success': False, 'message': f'An error occurred while deleting the user: {e}'}
        except Exception as e:
            return {'success': False, 'message': f'An unexpected error occurred: {e}'}
