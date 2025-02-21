from django.urls import path
import api.views.order_views as order_views

urlpatterns = [
    path("create", order_views.create_order,
         name="order_create_order"),
    path("status/<str:order_id>", order_views.update_order_status,
         name="order_update_order_status"),
    path("admin", order_views.get_all_orders,
         name="order_get_all_orders"),
    path("user", order_views.get_user_orders,
         name="order_get_user_orders"),

]
