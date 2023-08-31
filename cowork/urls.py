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

    path('chat/<slug:slug>/create_task/', views.create_task, name='create_task'),
    path('chat/<slug:slug>/comment/<int:task_id>/', views.comment_form, name='comment_task'),
    path('chat/<str:slug>/update_task/<int:task_id>/', views.update_task, name='update_task'),
    path('chat/<str:slug>/delete_task/<int:task_id>/', views.delete_task, name='delete_task'),
    path('chat/upload/<str:room_slug>/', views.upload_file, name='upload_file'),
    path('chat/list/<str:room_slug>/', views.file_list, name='file_list'),
    path('chat/access-log/<int:file_id>/', views.file_access_log, name='file_access_log'),

]
