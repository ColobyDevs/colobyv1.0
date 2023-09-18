from rest_framework import generics, permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from serializers.serializers import TaskSerializer, CommentSerializer, SendMessageSerializer, ReceiveMessageSerializer
from .models import Task, Comment
from .models import UploadedFile, FileAccessLog
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, reverse, redirect, get_object_or_404
from django.utils.text import slugify
import string
import random
from cowork.models import Room, Task, Message
from .forms import TaskForm, CommentForm


# private room
@login_required
def index(request, slug):
    room = Room.objects.get(slug=slug)
    messages = Message.objects.filter(room=room).order_by('created_at')
    # public_projects = Room.objects.filter(is_private=False)
    tasks = Task.objects.filter(room=room)

    return render(request, 'chat/room.html', {'name': room.name, 'messages': messages, 'slug': room.slug, 'tasks': tasks})


# public room
@login_required
def public_chat(request, slug):
    room = get_object_or_404(Room, slug=slug, is_private=False)
    public_projects = Room.objects.filter(is_private=False)
    messages = Message.objects.filter(room=room).order_by('created_at')
    tasks = Task.objects.filter(room=room)
    return render(request, 'chat/room.html', {'name': room.name, 'messages': messages, 'slug': room.slug, 'tasks': tasks, 'public_projects': public_projects})


@login_required
def room_create(request):
    if request.method == "POST":
        room_name = request.POST["room_name"]
        # Check if the room should be private
        is_private = request.POST.get("is_private") == "on"

        uid = str(''.join(random.choices(
            string.ascii_letters + string.digits, k=4)))
        room_slug = slugify(room_name + "_" + uid)
        room = Room.objects.create(
            name=room_name, slug=room_slug, is_private=is_private)

        if is_private:
            return redirect(reverse('chat', kwargs={'slug': room.slug}))
        else:
            return redirect(reverse('chat', kwargs={'slug': room.slug}))

    return render(request, 'chat/create.html')


@login_required
def room_join(request):
    if request.method == "POST":
        room_name = request.POST["room_name"]
        room = Room.objects.get(slug=room_name)
        return redirect(reverse('chat', kwargs={'slug': room.slug}))
    else:
        return render(request, 'chat/join.html')
    
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def send_message(request, room_slug):
    if request.method == "POST":
        serializer = SendMessageSerializer(data=request.data)
        if serializer.is_valid():
            user = request.user
            message_text = request.POST.get("message_text")

            room = Room.objects.get(slug=room_slug)
            message = Message.objects.create(room=room, user=user, message=message_text)

            return Response({"status": "Message successfully sent!"}, status=status.HTTP_201_CREATED)
        
        return Response({"error": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
    
    return Response({"error": "Invalid request method."}, status=status.HTTP_405_METHOD_NOT_ALLOWED)

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_message(request, room_slug):
    if request.method == "GET":
        room = Room.objects.get(slug=room_slug)
        messages = Message.objects.filter(room=room).order_by("created_at")

        # serializing each message to JSON
        serialized_messages = ReceiveMessageSerializer(messages, many=True).data

        return Response({"messages": serialized_messages}, status=status.HTTP_200_OK)
    
    return Response({"error": "Invalid request method."}, status=status.HTTP_405_METHOD_NOT_ALLOWED)
    
class TaskListCreateView(generics.ListCreateAPIView):
    queryset = Task.objects.all()
    serializer_class = TaskSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        room = get_object_or_404(Room, slug=self.kwargs['slug'])
        serializer.save(room=room)


class TaskRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Task.objects.all()
    serializer_class = TaskSerializer
    permission_classes = [permissions.IsAuthenticated]


class CommentCreateView(generics.CreateAPIView):
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer
    permission_classes = [permissions.IsAuthenticated]


class CommentRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer
    permission_classes = [permissions.IsAuthenticated]


@login_required
def upload_file(request, room_slug):
    if request.method == 'POST' and request.FILES.get('file'):
        uploaded_file = request.FILES['file']
        description = request.POST.get('description', '')
        room = get_object_or_404(Room, slug=room_slug)
        uploaded_file_instance = UploadedFile.objects.create(
            file=uploaded_file,
            room=room,
            uploaded_by=request.user,
            description=description
        )
        # You can optionally add a success message here
        return redirect('file_list', room_slug=room_slug)

    return render(request, 'file_manager/upload_file.html')


@login_required
def file_list(request, room_slug):
    room = get_object_or_404(Room, slug=room_slug)
    uploaded_files = UploadedFile.objects.filter(room=room)
    return render(request, 'file_manager/file_list.html', {'room': room, 'uploaded_files': uploaded_files})


@login_required
def file_access_log(request, file_id):
    uploaded_file = get_object_or_404(UploadedFile, id=file_id)
    access_logs = FileAccessLog.objects.filter(file=uploaded_file)
    return render(request, 'file_manager/file_access_log.html', {'uploaded_file': uploaded_file, 'access_logs': access_logs})
