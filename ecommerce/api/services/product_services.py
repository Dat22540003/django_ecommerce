from django.conf import settings


class ProductServices:
    def __init__(self):
        self.product_collection = settings.DB["products"]

    def get_all_products(self):
        products = self.product_collection.find()
        return list(products)
