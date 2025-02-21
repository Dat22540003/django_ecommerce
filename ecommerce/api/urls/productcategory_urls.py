from django.urls import path
import api.views.productcategory_views as productcategory_views

urlpatterns = [
    path("create", productcategory_views.create_productcategory,
         name="productcategory_create_productcategory"),
    path("get", productcategory_views.get_productcategories,
         name="productcategory_get_productcategories"),
    path("update/<str:productcategory_id>", productcategory_views.update_productcategory,
         name="productcategory_update_productcategory"),
    path("delete/<str:productcategory_id>", productcategory_views.delete_productcategory,
         name="productcategory_delete_productcategory"),
]
