from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/auth/", include('accounts.urls')),
    path("api/v1/", include('cowork.urls')),
    path('views', TemplateView.as_view(template_name='index.html')),
    path("accounts/", include("allauth.urls")),

    # DEBUG_TOOL_BAR
    path("__debug__/", include("debug_toolbar.urls")),
        
]
