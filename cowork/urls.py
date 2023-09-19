from django.urls import path
from django.views.generic import TemplateView
from cowork import views


urlpatterns = [
    path("", TemplateView.as_view(template_name="base.html"), name='index'),
    path("chat/room/<str:slug>/", views.index, name='chat'),
    path("create/", views.room_create, name='room-create'),
    path("join/", views.room_join, name='room-join'),
    path('public-room/<slug:slug>/', views.public_chat, name='public-room'),
    # path('post_message/', views.post_message, name='post-message'),
    path('room/<slug:slug>/tasks/', views.TaskListCreateView.as_view(), name='task-list'),
    path('room/tasks/<int:pk>/', views.TaskRetrieveUpdateDestroyView.as_view(), name='task-detail'),
    path('room/tasks/<int:pk>/comments/', views.CommentCreateView.as_view(), name='comment-create'),
    path('room/comments/<int:pk>/', views.CommentRetrieveUpdateDestroyView.as_view(), name='comment-detail'),

    path('chat/upload/<str:room_slug>/', views.upload_file, name='upload_file'),
    path('chat/list/<str:room_slug>/', views.file_list, name='file_list'),
    path('chat/access-log/<int:file_id>/', views.file_access_log, name='file_access_log'),
    path('api/chat/send/<slug:room_slug>/', views.send_message, name='send_message'), 
    path('api/chat/get/<slug:room_slug>/', views.get_message, name='get_message'), 

]
