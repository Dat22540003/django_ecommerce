from django.urls import path
import api.views.product_views as product_views

urlpatterns = [
    path("create", product_views.create_product,
         name="product_create_product"),
    path("", product_views.get_products,
         name="product_get_products"),
    path("get/<str:pid>", product_views.get_product,
         name="product_get_product"),
    path("update/<str:pid>", product_views.update_product,
         name="product_update_product"),
    path("delete/<str:pid>", product_views.delete_product,
         name="product_delete_product"),
    path("ratings", product_views.update_ratings, name="product_update_ratings"),
    path("uploadimages/<str:pid>", product_views.upload_images,
         name="product_upload_images"),
    path("variant/<str:pid>", product_views.add_variant,
         name="product_add_variant"),
]
