from django.conf import settings
from pymongo.errors import PyMongoError
from bson import ObjectId


class ProductcategoryServices:
    def __init__(self):
        self.productcategory_collection = settings.DB["productcategories"]

    # Create a new product category
    def create_productcategory(self, data):
        try:
            result = self.productcategory_collection.insert_one(data)
            if result.inserted_id is not None:
                return {'success': True, 'data': str(result.inserted_id)}
            else:
                return {'success': False, 'error': 'An error occurred while creating the product category.'}
        except PyMongoError as e:
            return {'success': False, 'error': f'An error occurred while creating the product category: {e}'}
        except Exception as e:
            return {'success': False, 'error': f'An unexpected error occurred: {e}'}

    # Get all product categories
    def get_productcategories(self):
        try:
            result = list(self.productcategory_collection.find())
            if result is None:
                return {'success': False, 'error': 'No product category found.'}
            else:
                return {'success': True, 'data': result}
        except PyMongoError as e:
            return {'success': False, 'error': f'An error occurred while getting the product categories: {e}'}
        except Exception as e:
            return {'success': False, 'error': f'An unexpected error occurred: {e}'}

    # Update product category
    def update_productcategory(self, update_by, data):
        try:
            result = self.productcategory_collection.update_one(
                update_by, {'$set': data})
            if result.modified_count > 0:
                return {'success': True, 'message': 'Product category updated successfully.'}
            else:
                return {'success': False, 'error': 'An error occurred while updating the product category.'}
        except PyMongoError as e:
            return {'success': False, 'error': f'An error occurred while updating the product category: {e}'}
        except Exception as e:
            return {'success': False, 'error': f'An unexpected error occurred: {e}'}

    # Delete product category
    def delete_productcategory(self, delete_by):
        try:
            result = self.productcategory_collection.delete_one(delete_by)
            if result.deleted_count > 0:
                return {'success': True, 'message': 'Product category deleted successfully.'}
            else:
                return {'success': False, 'error': 'An error occurred while deleting the product category.'}
        except PyMongoError as e:
            return {'success': False, 'error': f'An error occurred while deleting the product category: {e}'}
        except Exception as e:
            return {'success': False, 'error': f'An unexpected error occurred: {e}'}
