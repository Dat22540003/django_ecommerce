from api.services.product_services import ProductServices
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from api.common.utils import convert_to_json_compatible


class ProductView(APIView):
    services = ProductServices()

    def get(self, request):
        products = self.services.get_all_products()

        products = convert_to_json_compatible(products)
        return Response({"productData": products}, status=status.HTTP_200_OK)
