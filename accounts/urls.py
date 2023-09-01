from django.urls import path
from django.contrib.auth import views as auth_views
import accounts.views as user_views
from accounts import views

urlpatterns = [
    path("register/", views.register_user, name="register"),
    
    path(
        "login/",
        auth_views.LoginView.as_view(template_name="accounts/login.html"),
        name="login",
    ),
    path(
        "logout/",
        auth_views.LogoutView.as_view(template_name="accounts/logout.html"),
        name="logout",
    ),
]
