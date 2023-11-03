from django.urls import path
from django.contrib.auth import views as auth_views
import accounts.views as user_views
from accounts.views import (
    UserRegistrationView,
    LogoutView, 
    GoogleLogin, 
    SignInAPIView, 
    ChangePasswordView,
)
from . import views


urlpatterns = [
    path("register/", UserRegistrationView.as_view(), name="register"),
    
    path("log-in/", SignInAPIView.as_view(), name="log-in"),
    path("change-password/", ChangePasswordView.as_view(), name="change_password"),
    path(
        "logout/",
        auth_views.LogoutView.as_view(template_name="accounts/logout.html"),
        name="logout",
    ),
    path('log-out/', LogoutView.as_view(), name="log-out"),

    # OAUTH LOGINS
    path("google-login/", GoogleLogin.as_view(), name="google-login"),

]

