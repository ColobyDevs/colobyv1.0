from django.urls import path
from django.contrib.auth import views as auth_views
import accounts.views as user_views
from accounts.views import register_user, SignInAPIView
from . import views
from accounts import views
 

urlpatterns = [
    path("register/", views.register_user, name="register"),
    
    path("log-in/", SignInAPIView.as_view(), name="log-in"),
    path(
        "logout/",
        auth_views.LogoutView.as_view(template_name="accounts/logout.html"),
        name="logout",
    ),
]
