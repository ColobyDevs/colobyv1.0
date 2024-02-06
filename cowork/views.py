from rest_framework import status
from rest_framework import generics, permissions, status, viewsets
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.renderers import JSONRenderer
from rest_framework.views import APIView
from serializers.serializers import (
    TaskSerializer, CommentSerializer,
    SendMessageSerializer, ReceiveMessageSerializer,
    RoomSerializer,
    BranchSerializer, UserNoteSerializer,
    FeatureRequestSerializer,
    UploadedFileSerializer

)
from .models import (Task, Comment, Room, Message,
                     UploadedFile,
                     FileAccessLog, Branch,
                     UserNote, FeatureRequest
                     )


from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render, reverse, redirect, get_object_or_404
from django.utils.text import slugify
from django.utils.decorators import method_decorator
from django.http import HttpResponse, Http404, FileResponse, HttpResponseBadRequest, HttpResponseForbidden, JsonResponse
from django.urls import reverse
from django.db.models import Q
from django.core.exceptions import ValidationError, FieldError
from django.core.paginator import Paginator
from .forms import TaskForm, CommentForm, UploadedFileForm, BranchForm
import string
import random
import mimetypes


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow the owner of an object to edit it.
    """

    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request, so we'll always allow GET, HEAD, or OPTIONS requests.
        if request.method in permissions.SAFE_METHODS:
            return True

        # Write permissions are only allowed to the owner of the object.
        return obj.owner == request.user

# private room


@login_required
def index(request, slug):
    room = Room.objects.get(slug=slug)
    messages = Message.objects.filter(room=room).order_by('created_at')
    # public_projects = Room.objects.filter(is_private=False)
    tasks = Task.objects.filter(room=room)

    return render(request, 'chat/room.html', {'name': room.name, 'messages': messages, 'slug': room.slug, 'tasks': tasks})


@login_required
def public_chat(request, slug):
    """
    Displays a public chat room.

    Args:
        request: The HTTP request.
        slug: The slug of the chat room.

    Returns:
        A rendered HTML response.
    """

    try:
        room = get_object_or_404(Room, slug=slug, is_private=False)
        public_projects = Room.objects.filter(is_private=False)
        messages = Message.objects.filter(room=room).order_by('created_at')
        tasks = Task.objects.filter(room=room)
        return render(request, 'chat/room.html', {'name': room.name, 'messages': messages, 'slug': room.slug, 'tasks': tasks, 'public_projects': public_projects})
    except Room.DoesNotExist:
        return HttpResponse("Room not found!", status=404)
    except Exception as e:
        print(f"An error occurred {str(e)}")
        return HttpResponse("An error occured", status=500)


class RoomViewSet(viewsets.ModelViewSet):
    queryset = Room.objects.all()
    serializer_class = RoomSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class RoomDetail(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, unique_link):
        try:
            room = Room.objects.get(unique_link=unique_link)
            if room.is_private and request.user not in room.users.all():
                return Response({"detail": "You do not have access to this room."}, status=status.HTTP_403_FORBIDDEN)
            serializer = RoomSerializer(room)
            return Response(serializer.data)
        except Room.DoesNotExist:
            return Response({"detail": "Room not found."}, status=status.HTTP_404_NOT_FOUND)


@login_required
def room_create(request):
    """
    Creates a new chat room.

    Args:
        request: The HTTP request.

    Returns:
        A rendered HTML response, or a redirect to the new chat room.
    """
    if request.method == "POST":
        room_name = request.POST.get("room_name")
        is_private = request.POST.get("is_private") == "on"
        if not room_name:
            messages.error(request, "Room name is required!")
            return redirect(reverse('create-room'))
        try:
            uid = str(''.join(random.choices(
            string.ascii_letters + string.digits, k=4)))
            room_slug = slugify(room_name + "_" + uid)
            room = Room.objects.create(
                name=room_name,
                slug=room_slug,
                is_private=is_private,
                created_by=request.user)

            if is_private:
                return redirect(reverse('chat', kwargs={'unique_link': room.unique_link}))
            else:
                return redirect(reverse('chat', kwargs={'unique_link': room.unique_link}))

        except Exception as e:
                messages.error(request, "An error occurred during room creation")
                return redirect(reverse('create-room'))

    return render(request, 'chat/create.html')


@login_required
def room_join(request):
    """
    Joins a chat room.

    Args:
        request: The HTTP request.

    Returns:
        A redirect to the chat room, or raises an error if the room does not exist or the 
        user does not have permission to join it.
    """
    if request.method == "POST":
        room_name = request.POST.get("room_name")
        try:
            room = Room.objects.get(slug=room_name)
        except Room.DoesNotExist:
            messages.error(request, "Room does not exist!")
            return HttpResponse(status=500)

        if not room.is_private or request.user in room.users.all():
            return redirect(reverse('chat', kwargs={'slug': room.slug}))
        else:
            messages.error(request, "Access denied, this is a private room!")
            return HttpResponseForbidden("Access denied, this is a private room!")

    return HttpResponseBadRequest("Unable to join the room.")

  
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def send_message(request, room_slug):
    """Sends a message to a chat room, including media upload (optional).

    Args:
        request: The HTTP request.
        room_slug: The slug of the chat room.

    Returns:
        A JSON response with the status of the message send, or an error response if the request is invalid.
    """
    if request.method == "POST":
        serializer = SendMessageSerializer(data=request.data)
        if serializer.is_valid():
            user = request.user
            room = Room.objects.get(slug=room_slug)
            media_file = request.data.get("media_file")
            
            if media_file:
                media_msg = Message.objects.create(room=room, user=user, media=media_file)


            message_text = serializer.validated_data.get("message_text")
            
            if message_text:
                try:
                    message = Message.objects.create(room=room, user=user, message=message_text)
                    return Response({"status": "Message successfully sent!"}, status=status.HTTP_201_CREATED)
                except Room.DoesNotExist:
                    raise Http404("Room does not exist!")
                except Exception as e:
                    messages.error(f"Error occurred: {str(e)}")
                    return HttpResponse(status=500)
            

            try:
                room = Room.objects.get(slug=room_slug)
                message = Message.objects.create(
                    room=room, user=user, message=message_text)
                return Response({"status": "Message successfully sent!"}, status=status.HTTP_201_CREATED)
            except Room.DoesNotExist:
                raise Http404("Room does not exist!")
            except Exception as e:
                messages.error(f"Error occurred: {str(e)}")
                return HttpResponse(status=500)


        return Response({"error": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    return Response({"error": "Invalid request method."}, status=status.HTTP_405_METHOD_NOT_ALLOWED)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_message(request, room_slug):
    """Gets all messages from a chat room.

    Args:
        request: The HTTP request.
        room_slug: The slug of the chat room.

    Returns:
        A JSON response with a list of messages, or an error response if the request is invalid.
    """
    if request.method == "GET":
        try:
            room = Room.objects.get(slug=room_slug)
            messages = Message.objects.filter(room=room).order_by("created_at")

            serialized_messages = ReceiveMessageSerializer(
                messages, many=True).data

            return Response({"messages": serialized_messages}, status=status.HTTP_200_OK)
        except Room.DoesNotExist:
            raise Http404("Room does not exist!")
        except Exception as e:
            messages.error(f"Error occurred: {str(e)}")
            return HttpResponse(status=500)

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


class UserNoteCreateView(generics.ListCreateAPIView):
    queryset = UserNote.objects.all()
    serializer_class = UserNoteSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]

    def perform_create(self, serializer):
        return serializer.save(user=self.request.user)


class UserNoteRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    queryset = UserNote.objects.all()
    serializer_class = UserNoteSerializer
    permission_classes = [IsAuthenticated]


class FeatureRequestListCreateView(generics.ListCreateAPIView):
    serializer_class = FeatureRequestSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        room_id = self.kwargs['room_id']
        user_id = self.request.user.id
        return FeatureRequest.objects.filter(room=room_id, user=user_id)

    def perform_create(self, serializer):
        room_id = self.kwargs['room_id']
        serializer.save(room_id=room_id, user=self.request.user)


class FeatureRequestRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    queryset = FeatureRequest.objects.all()
    serializer_class = FeatureRequestSerializer


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def like_room(request, room_slug):
    try:
        room = Room.objects.get(slug=room_slug)
        user = request.user

        if user in room.likes.all():
            room.likes.remove(user)
            return Response({"message": "Room unliked successfully."}, status=status.HTTP_200_OK)
        else:
            room.likes.add(user)
            return Response({"message": "Room liked successfully."}, status=status.HTTP_200_OK)
    except Room.DoesNotExist:
        return Response({"error": "Room not found."}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class IsUploaderOrReadOnly(permissions.BasePermission):
    """
    Custom permission class to only allow the uploader of the file to  make changes to said file.
    """

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True

        return obj.uploaded_by == request.user


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def upload_file(request, room_slug):
    """
    Uploads a file to a chat room.

    Args:
        request: The HTTP request.
        room_slug: The slug of the chat room.

    Returns:
        A JSON response with the status of the file upload, or an error response if the request is invalid.
    """
    if request.method == 'POST' and request.FILES.get('file'):
        try:
            uploaded_file = request.FILES['file']
            description = request.POST.get('description', '')
            room = get_object_or_404(Room, slug=room_slug)
            uploaded_file_instance = UploadedFile.objects.create(
                file=uploaded_file,
                room=room,
                uploaded_by=request.user,
                description=description
            )

            # return redirect('file_list', room_slug=room_slug)
            return Response({"status": "File uploaded successfully."}, status=status.HTTP_200_OK)

        except Room.DoesNotExist:
            raise Http404("Room does not exist!")
        except Exception as e:
            messages.error(f"Error occurred: {str(e)}")
            return HttpResponse(status=500)

    # return render(request, 'file_manager/upload_file.html')
    return Response({"error": "Invalid request method!"}, status=status.HTTP_405_METHOD_NOT_ALLOWED)


class UploadFileView(generics.CreateAPIView):
    queryset = UploadedFile.objects.all()
    serializer_class = UploadedFileSerializer
    parser_classes = (MultiPartParser, FormParser)
    permission_classes = [permissions.IsAuthenticated, IsUploaderOrReadOnly]

    def perform_create(self, serializer):
        serializer.save(uploaded_by=self.request.user)


class BranchList(generics.ListCreateAPIView):
    queryset = Branch.objects.all()
    serializer_class = BranchSerializer


class BranchDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Branch.objects.all()
    serializer_class = BranchSerializer


@method_decorator(login_required, name="dispatch")
class FileListAPIView(APIView):
    """
    Lists all files in a chat room.

    Args:
        request: The HTTP request.
        room_slug: The slug of the chat room.

    Returns:
        A JSON response with a list of files in the chat room, or an error response if the request is invalid.
    """
    renderer_classes = [JSONRenderer]

    def get(self, request, room_slug):
        try:
            room = get_object_or_404(Room, slug=room_slug)
            uploaded_files = UploadedFile.objects.filter(room=room)
            serializer = UploadedFileSerializer(uploaded_files, many=True)
            # return render(request, 'file_manager/file_list.html', {'room': room, 'uploaded_files': uploaded_files})
            return Response({"status": "You are viewing files now", "files": serializer.data}, status=status.HTTP_200_OK)
        except Room.DoesNotExist:
            raise Http404("Room does not exist!")
        except Exception as e:
            messages.error(f"Error occurred: {str(e)}")
            return HttpResponse(status=500)


@login_required
def file_download(request, room_slug, file_id):
    """
    Downloads a file from a chat room.

    Args:
        request: The HTTP request.
        room_slug: The slug of the chat room.
        file_id: The ID of the file to download.

    Returns:
        A FileResponse object with the file content, or an error response if the request is invalid.
    """
    try:
        room = get_object_or_404(Room, slug=room_slug)
        upload_file = get_object_or_404(UploadedFile, id=file_id, room=room)
        file_path = upload_file.file.path
        content_type, _ = mimetypes.guess_type(file_path)

        if upload_file.uploaded_by == request.user or request.user in room.users.all():
            response = FileResponse(
                open(file_path, 'rb'), content_type='application/octet-stream')
            response['Content-Type'] = content_type
            response['Content-Disposition'] = f'attachment; filename="{upload_file.file.name}"'
            return response
        else:
            return HttpResponse("Access Denied!", status=403)

    except Room.DoesNotExist:
        raise Http404("Room does not exist!")
    except UploadedFile.DoesNotExist:
        raise Http404("File does not exist!")
    except Exception as e:
        messages.error(f"Error occurred: {str(e)}")
        return HttpResponse(status=500)


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def edit_uploaded_file(request, file_id):
    """
    Edit an uploaded file.

    Args:
        request: The HTTP request.
        file_id: The ID of the uploaded file to edit.

    Returns:
        A redirect response to the file detail page IF the form is valid or
        a render response to the edit uploaded file for invalid form.

    """
    try:
        upload_file = get_object_or_404(UploadedFile, id=file_id)

        # if request.user != upload_file.owner:
        #     raise PermissionDenied()

        if request.method == 'POST':
            form = UploadedFileForm(request.POST, instance=upload_file)
            if form.is_valid():
                form.save()
                # return redirect("file_detail", file_id=file_id)
                return Response({"status": "File edited successfully"}, status=status.HTTP_200_OK)
            else:
                return Response({"error": "Form data is invalid"}, status=status.HTTP_400_BAD_REQUEST)
        else:
            form = UploadedFileForm(instance=upload_file)
            # return render(request, "file_manager/edit_uploaded_file.html", {"form": form, "upload_file": upload_file})
            return Response({"status": "You are editing this file now"}, status=status.HTTP_200_OK)
    except Exception as e:
        # messages.error(f"Error occurred: {str(e)}")
        # return HttpResponse(status=500)
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@login_required
def file_access_log(request, file_id):
    uploaded_file = get_object_or_404(UploadedFile, id=file_id)
    access_logs = FileAccessLog.objects.filter(file=uploaded_file)
    return render(request, 'file_manager/file_access_log.html', {'uploaded_file': uploaded_file, 'access_logs': access_logs})

@login_required
def search(request):
    """Performs a search across multiple models and returns results in JSON format.

    Requires authentication.

    Args:
    request (HttpRequest): The incoming HTTP request.

    Returns:
    JsonResponse: A JSON response containing search results for rooms, files, tasks, branches, and messages.

    Raises:
    ValueError: If the 'q' query parameter is not provided in the request.
    """
    try:
        query = request.GET.get('q', '')
        if not query:
            raise ValueError("The 'q' parameter is required.")

        all_results = []
        all_results.extend(Room.objects.filter(Q(name__icontains=query)))
        all_results.extend(UploadedFile.objects.filter(Q(file__icontains=query)))
        all_results.extend(Task.objects.filter(Q(title__icontains=query)))
        all_results.extend(Branch.objects.filter(Q(original_file__icontains=query)))
        all_results.extend(Message.objects.filter(Q(message__icontains=query)))

        paginator = Paginator(all_results, 25)
        page_number = request.GET.get('page', 1)
        page_obj = paginator.get_page(page_number)

        return JsonResponse({
            'results': [{'id': result.id, 'name': result.name} if isinstance(result, Room) else
                        {'id': result.id, 'file': result.file.name} if isinstance(result, UploadedFile) else
                        {'id': result.id, 'title': result.title} if isinstance(result, Task) else
                        {'id': result.id, 'branch': result.original_file.file.name} if isinstance(result, Branch) else
                        {'id': result.id, 'message': result.message} for result in page_obj],
        })

    except ValidationError as ve:
        return JsonResponse({'error': str(ve)}, status=400)
    
    except FieldError as fe:
        return JsonResponse({'error': str(fe)}, status=400)

    except Exception as e:
        return JsonResponse({'error': f"An unexpected error occurred: {str(e)}"}, status=500)

# search for each room, file uploaded, task, branch, message***