from django.conf import settings
from pymongo.errors import PyMongoError
from bson import ObjectId


class ProductServices:
    def __init__(self):
        self.product_collection = settings.DB["products"]

    # Create a new product
    def create_product(self, data):
        try:
            result = self.product_collection.insert_one(data)

            if result.inserted_id is not None:
                return {'success': True, 'data': str(result.inserted_id)}
            else:
                return {'success': False, 'error': 'An error occurred while creating the product.'}
        except PyMongoError as e:
            return {'success': False, 'error': f'An error occurred while creating the product: {e}'}
        except Exception as e:
            return {'success': False, 'error': f'An unexpected error occurred: {e}'}

    # Get all products
    def get_products(self, query_data):
        try:
            result = None
            if 'fields' not in query_data and 'sort' not in query_data:
                result = list(self.product_collection.find(query_data['find']).skip(
                    query_data['skip']).limit(query_data['limit']))
            elif 'sort' not in query_data:
                result = list(self.product_collection.find(query_data['find'], query_data['fields']).skip(
                    query_data['skip']).limit(query_data['limit']))
            elif 'fields' not in query_data:
                result = list(self.product_collection.find(query_data['find']).sort(
                    query_data['sort']).skip(query_data['skip']).limit(query_data['limit']))
            else:
                result = list(self.product_collection.find(query_data['find'], query_data['fields']).sort(
                    query_data['sort']).skip(query_data['skip']).limit(query_data['limit']))
            if result is None:
                return {'success': False, 'error': f'No product found with the given query data.'}
            else:
                return {'success': True, 'data': result}
        except PyMongoError as e:
            return {'success': False, 'error': f'An error occurred while getting the products: {e}'}
        except Exception as e:
            return {'success': False, 'error': f'An unexpected error occurred: {e}'}

    # Get a single product
    def get_product(self, pid):
        try:
            pipeline = [
                {
                    '$match': {
                        '_id': ObjectId(pid)
                    }
                },
                {
                    '$lookup': {
                        'from': 'users',
                        'localField': 'ratings.postedBy',
                        'foreignField': '_id',
                        'as': 'ratingDetails'
                    }
                },
                {
                    '$project': {
                        'title': 1,
                        'slug': 1,
                        'description': 1,
                        'brand': 1,
                        'thumb': 1,
                        'price': 1,
                        'category': 1,
                        'quantity': 1,
                        'sold': 1,
                        'images': 1,
                        'color': 1,
                        'ratings': {
                            '$map': {
                                'input': '$ratings',
                                'as': 'rating',
                                'in': {
                                    '$mergeObjects': [
                                        '$$rating',
                                        {
                                            '$let': {
                                                'vars': {
                                                    'user': {
                                                        '$arrayElemAt': [
                                                            {
                                                                '$filter': {
                                                                    'input': '$ratingDetails',
                                                                    'as': 'user',
                                                                    'cond': {
                                                                        '$eq': ['$$user._id', '$$rating.postedBy']
                                                                    }
                                                                }
                                                            },
                                                            0
                                                        ]
                                                    }
                                                },
                                                'in': {
                                                    'firstname': '$$user.firstname',
                                                    'lastname': '$$user.lastname',
                                                    'avatar': '$$user.avatar'
                                                }
                                            }
                                        }
                                    ]
                                }
                            }
                        },
                        'totalRating': 1,
                        'variant': 1,
                        'createdAt': 1,
                        'updatedAt': 1
                    }
                }
            ]

            # Execute the pipeline
            result = list(self.product_collection.aggregate(pipeline))

            if result is None:
                return {'success': False, 'error': f'No product found with the given ID.'}
            else:
                return {'success': True, 'data': result[0]}
        except PyMongoError as e:
            return {'success': False, 'error': f'An error occurred while getting the product: {e}'}
        except Exception as e:
            return {'success': False, 'error': f'An unexpected error occurred: {e}'}

    # Update a product
    def update_product(self, update_by, data):
        try:
            result = self.product_collection.update_one(
                update_by, {'$set': data, '$currentDate': {'updatedAt': True}})

            if result.modified_count == 1:
                return {'success': True, 'message': 'Product updated successfully'}
            else:
                return {'success': False, 'error': 'An error occurred while updating the product.'}
        except PyMongoError as e:
            return {'success': False, 'error': f'An error occurred while updating the product: {e}'}
        except Exception as e:
            return {'success': False, 'error': f'An unexpected error occurred: {e}'}

    # Delete a product
    def delete_product(self, delete_by):
        try:
            result = self.product_collection.delete_one(delete_by)

            if result.deleted_count == 1:
                return {'success': True, 'message': 'Product deleted successfully'}
            else:
                return {'success': False, 'error': 'An error occurred while deleting the product.'}
        except PyMongoError as e:
            return {'success': False, 'error': f'An error occurred while deleting the product: {e}'}
        except Exception as e:
            return {'success': False, 'error': f'An unexpected error occurred: {e}'}

    # Update ratings
    def update_ratings(self, update_by, state, data):
        try:
            result = None

            if state == 'MODIFY':
                result = self.product_collection.update_one(
                    update_by,
                    {'$set': {
                        'ratings.$.star': int(data['star']), 'ratings.$.comment': data['comment'], 'ratings.$.updatedAt': data['updatedAt']}}
                )
            elif state == 'ADD':
                result = self.product_collection.update_one(
                    update_by,
                    {'$push': {'ratings': data}}
                )

            if result.modified_count == 1:
                return {'success': True, 'message': 'Ratings updated successfully'}
            else:
                return {'success': False, 'error': 'An error occurred while updating the ratings.'}
        except PyMongoError as e:
            return {'success': False, 'error': f'An error occurred while updating the ratings: {e}'}
        except Exception as e:
            return {'success': False, 'error': f'An unexpected error occurred: {e}'}

    # Upload images
    def upload_images(self, update_by, data):
        try:
            result = self.product_collection.update_one(
                update_by,
                {'$push': {'images': {'$each': data}},
                    '$currentDate': {'updatedAt': True}}
            )
            if result.modified_count == 1:
                return {'success': True, 'message': 'Images uploaded successfully'}
            else:
                return {'success': False, 'error': 'An error occurred while uploading the images.'}
        except PyMongoError as e:
            return {'success': False, 'error': f'An error occurred while uploading the images: {e}'}
        except Exception as e:
            return {'success': False, 'error': f'An unexpected error occurred: {e}'}

    # Add variant
    def add_variant(self, update_by, data):
        try:
            result = self.product_collection.update_one(
                update_by,
                {'$push': {'variant': data},
                    '$currentDate': {'updatedAt': True}}
            )
            if result.modified_count == 1:
                return {'success': True, 'message': 'Variant added successfully'}
            else:
                return {'success': False, 'error': 'An error occurred while adding the variant.'}
        except PyMongoError as e:
            return {'success': False, 'error': f'An error occurred while adding the variant: {e}'}
        except Exception as e:
            return {'success': False, 'error': f'An unexpected error occurred: {e}'}
