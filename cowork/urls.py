from django.urls import path
from . import views

urlpatterns = [
    path('create/', views.create_project, name='create_project'),
    path('<uuid:project_id>/', views.project_detail, name='project_detail'),
    path('join/<uuid:project_id>/', views.join_project, name='join_project'),
]
