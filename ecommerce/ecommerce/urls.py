from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/product/", include("api.urls.product_urls")),
    path("api/user/", include("api.urls.user_urls")),
]
