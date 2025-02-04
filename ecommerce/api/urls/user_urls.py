from django.urls import path
import api.views.user_views as user_views

urlpatterns = [

    # Authentication
    path("register", user_views.register, name="user_register"),
    path("completeregister/<str:token>",
         user_views.complete_register, name="user_complete_register"),
    path("login", user_views.login, name="user_login"),
    path("logout", user_views.logout, name="user_logout"),
    path("refreshtoken", user_views.refresh_access_token,
         name="user_refresh_access_token"),


    # Password management
    path("forgotpassword", user_views.forgot_password,
         name="user_forgot_password"),
    path("resetpassword", user_views.reset_password, name="user_reset_password"),


    # User management
    path("", user_views.get_users, name="user_get_users"),
    path("current", user_views.get_current, name="user_get_curent"),
    path("<str:user_id>", user_views.delete_user, name="user_delete_user"),


    # User update
    path("update/address", user_views.update_user_address,
         name="user_update_user_address"),
    path("update/current", user_views.update_user, name="user_update_user"),
    path("update/<str:user_id>", user_views.update_user_by_admin,
         name="user_update_user_by_admin"),
]
