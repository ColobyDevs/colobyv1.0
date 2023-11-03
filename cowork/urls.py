from django.urls import path
from django.views.generic import TemplateView
from cowork import views


urlpatterns = [
    path("", TemplateView.as_view(template_name="base.html"), name='index'),
    path("chat/room/<str:unique_link>/", views.index, name='chat'),
    path("create/", views.room_create, name='room-create'),
    path("join/", views.room_join, name='room-join'),
    path('public-room/<slug:slug>/', views.public_chat, name='public-room'),
    # path('post_message/', views.post_message, name='post-message'),
    path('room/<slug:slug>/tasks/', views.TaskListCreateView.as_view(), name='task-list'),
    path('room/tasks/<int:pk>/', views.TaskRetrieveUpdateDestroyView.as_view(), name='task-detail'),
    path('room/tasks/<int:pk>/comments/', views.CommentCreateView.as_view(), name='comment-create'),
    path('room/comments/<int:pk>/', views.CommentRetrieveUpdateDestroyView.as_view(), name='comment-detail'),
    path('room/like/<str:room_slug>/', views.like_room, name='like-room'),

    # usernote endpoints (To F.Es the feature requires autosave 😉)
    path('user/notes/', views.UserNoteCreateView.as_view(), name='usernote-list-create'),
    path('user/notes/<int:pk>/', views.UserNoteRetrieveUpdateDestroyView.as_view(), name='usernote-retrieve-update-destroy'),


    # feature requests
    path('rooms/<int:room_id>/feature-requests/', views.FeatureRequestListCreateView.as_view(), name='feature-request-list-create'),
    path('rooms/<int:room_id>/feature-requests/<int:pk>/', views.FeatureRequestRetrieveUpdateDestroyView.as_view(), name='feature-request-retrieve-update-destroy'),

    # file upload endpoints
    path('chat/upload/<str:room_slug>/', views.upload_file, name='upload-file'),
    path('chat/list/<str:room_slug>/', views.FileListAPIView.as_view(), name='file-list'),
    path('api/branches/', views.BranchList.as_view(), name='branch-list'),
    path('api/branches/<int:pk>/', views.BranchDetail.as_view(), name='branch-detail'),
    
    path('chat/download/<str:room_slug>/<int:file_id>/', views.file_download, name='file-download'),
    path('api/v1/chat/edit-uploaded-file/<int:file_id>', views.edit_uploaded_file, name='edit-uploaded-file'),
    path('chat/access-log/<int:file_id>/', views.file_access_log, name='file_access_log'),
    path('api/chat/send/<slug:room_slug>/', views.send_message, name='send-message'), 
    path('api/chat/get/<slug:room_slug>/', views.get_message, name='get-message'),
    path('api/room/create/', views.RoomViewSet.as_view({'post': 'create'})),
    path('api/room/<int:pk>/', views.RoomDetail.as_view(), name='room-detail'),
]