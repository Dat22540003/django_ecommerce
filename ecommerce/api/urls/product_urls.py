from django.urls import path
from api.views.product_views import ProductView

urlpatterns = [
    path("", ProductView.as_view(), name="product"),

]
