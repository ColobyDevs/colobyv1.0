import string
import random
import mimetypes
from serializers.serializers import UploadedFileSerializer, BranchSerializer, UploadedFileVersionSerializer, CommitSerializer
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render, reverse, redirect, get_object_or_404
from django.utils.text import slugify
from django.utils.decorators import method_decorator
from django.http import HttpResponse, Http404, FileResponse, HttpResponseBadRequest, HttpResponseForbidden
from django.urls import reverse
from django.contrib import messages
from rest_framework import status, generics, permissions, status, viewsets
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
    # BranchSerializer,
    UserNoteSerializer,
    FeatureRequestSerializer,
    # UploadedFileSerializer,
    Commit, UploadedFileVersion

)
from .models import (Task, Comment, Room, Message,
                     UploadedFile,
                     #  FileAccessLog,
                     Branch,
                     UserNote, FeatureRequest
                     )




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




# @login_required
# def index(request, slug):
#     room = Room.objects.get(slug=slug)
#     messages = Message.objects.filter(room=room).order_by('created_at')
#     # public_projects = Room.objects.filter(is_private=False)
#     tasks = Task.objects.filter(room=room)

#     return render(request, 'chat/room.html', {'name': room.name, 'messages': messages, 'slug': room.slug, 'tasks': tasks})


class RoomCreateJoinView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        action = request.data.get("action")
        if action == "create":
            return self.create_room(request)
        elif action == "join":
            return self.join_room(request)
        else:
            return Response({"detail": "Invalid action."}, status=status.HTTP_400_BAD_REQUEST)

    def create_room(self, request):
        room_name = request.data.get("room_name")
        description = request.data.get("description")
        is_private = request.data.get("is_private", False)

        if not room_name:
            return Response({"detail": "Room name is required!"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            uid = str(''.join(random.choices(
                string.ascii_letters + string.digits, k=4)))
            room_slug = slugify(room_name + "_" + uid)
            room = Room.objects.create(
                name=room_name,
                slug=room_slug,
                description=description,
                is_private=is_private,
                created_by=request.user
            )

            serializer = RoomSerializer(room)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({"detail": "An error occurred during room creation"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def join_room(self, request):
        provided_slug = request.data.get("room_slug")
        try:
            room = Room.objects.get(slug=provided_slug)
        except Room.DoesNotExist:
            return Response({"detail": "Room does not exist!"}, status=status.HTTP_404_NOT_FOUND)

        correct_slug = room.slug  # Actual slug for the room

        if provided_slug == correct_slug:
            # The provided slug matches the actual slug, proceed to join the room
            if not room.is_private or request.user in room.users.all():
                # Add the user to the room's users
                room.users.add(request.user)

                return Response({"detail": "Successfully joined the room."}, status=status.HTTP_200_OK)
            else:
                return Response({"detail": "Access denied, this is a private room!"}, status=status.HTTP_403_FORBIDDEN)
        else:
            # The provided slug does not match the actual slug
            return Response({"detail": "Invalid passcode for the room!"}, status=status.HTTP_400_BAD_REQUEST)
        
        def delete_room(self, request):
            room_slug = request.data.get("room_slug")
            try:
                room = Room.objects.get(slug=room_slug)
            except Room.DoesNotExist:
                return Response({"detail": "Room does not exist!"}, status=status.HTTP_404_NOT_FOUND)

            if room.created_by == request.user:
                room.delete()
                return Response({"detail": "Room deleted successfully."}, status=status.HTTP_200_OK)
            else:
                return Response({"detail": "You are not the creator of this room, so you cannot delete it."},
                            status=status.HTTP_403_FORBIDDEN)


class RoomDetailView(APIView):
    permission_classes = [IsAuthenticated, IsOwnerOrReadOnly]

    def get(self, request, room_slug):
        try:
            room = Room.objects.get(slug=room_slug)
            if room.is_private and request.user not in room.users.all():
                return Response({"detail": "You do not have access to this room."}, status=status.HTTP_403_FORBIDDEN)
            serializer = RoomSerializer(room)
            return Response(serializer.data)
        except Room.DoesNotExist:
            return Response({"detail": "Room not found."}, status=status.HTTP_404_NOT_FOUND)


# class UserRoomsView(APIView):
#     permission_classes = [IsAuthenticated]
#     def get(self, request):
#         user = request.user
#         created_rooms = user.get_created_rooms()
#         joined_rooms = user.get_joined_rooms()

#         # Now, you have the rooms created and joined by the user
#         data = {
#             'created_rooms': created_rooms.values(),
#             'joined_rooms': joined_rooms.values(),
#         }

#         return Response(data, status=status.HTTP_200_OK)


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
        # Set room and user based on the request context
        room = Room.objects.get(slug=room_slug)
        user = request.user

        # Include room and user in the request data
        request.data["room"] = room.id
        request.data["user"] = user.id

        serializer = SendMessageSerializer(data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response({"status": "Message successfully sent!"}, status=status.HTTP_201_CREATED)

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
        room = get_object_or_404(Room, slug=self.kwargs['room_slug'])
        serializer.save(room=room)

    def get_serializer_context(self):
        # Pass the room to the serializer context
        context = super().get_serializer_context()
        context['room'] = get_object_or_404(
            Room, slug=self.kwargs['room_slug'])
        return context


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


class UploadFileView(generics.CreateAPIView):
    queryset = UploadedFile.objects.all()
    serializer_class = UploadedFileSerializer
    parser_classes = (MultiPartParser, FormParser)
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        # Get the room slug from the URL parameters
        room_slug = self.kwargs.get('room_slug', None)

        # Get the room instance
        room = get_object_or_404(Room, slug=room_slug)

        # Associate the room with the UploadedFile instance
        serializer.validated_data['room'] = room

        # Save the UploadedFile instance
        uploaded_file_instance = serializer.save(uploaded_by=self.request.user)

        # Create initial commit for the master branch
        master_branch, created = Branch.objects.get_or_create(
            original_file=uploaded_file_instance,
            created_by=self.request.user,
            room=room  
        )


        # Create a commit for the uploaded file
        commit = Commit.objects.create(
            branch=master_branch,
            uploader=self.request.user,
            description="Initial commit"
        )

        # Create a version for the master branch
        UploadedFileVersion.objects.create(
            uploaded_file=uploaded_file_instance,
            commit=commit,
            file=uploaded_file_instance.file,
            description=uploaded_file_instance.description,
            file_size=uploaded_file_instance.file_size
        )




class SwitchBranchView(APIView):
    """
    Switches to the specified branch.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, room_slug, file_id, branch_id):
        try:
            uploaded_file = get_object_or_404(
                UploadedFile, id=file_id, room__slug=room_slug)
            branch = get_object_or_404(
                Branch, id=branch_id, original_file=uploaded_file)

            # Implement logic to switch to the specified branch
            # For example, you can update the UploadedFile instance to use the latest version from the branch
            latest_version = UploadedFileVersion.objects.filter(
                uploaded_file=uploaded_file, commit__branch=branch).latest('commit__timestamp')
            uploaded_file.file = latest_version.file
            uploaded_file.description = latest_version.description
            uploaded_file.file_size = latest_version.file_size
            uploaded_file.save()

            return Response({"status": "Switched to branch successfully."}, status=status.HTTP_200_OK)

        except UploadedFile.DoesNotExist:
            raise Http404("File does not exist!")
        except Branch.DoesNotExist:
            raise Http404("Branch does not exist!")
        except UploadedFileVersion.DoesNotExist:
            raise Http404("File version not found!")
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class BranchList(generics.ListCreateAPIView):
    serializer_class = BranchSerializer

    def get_queryset(self):
        # Get the room slug from the URL parameters
        room_slug = self.kwargs.get('room_slug', None)
        return Branch.objects.filter(original_file__room__slug=room_slug)


class BranchDetail(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = BranchSerializer

    def get_queryset(self):
        # Get the room slug from the URL parameters
        room_slug = self.kwargs.get('room_slug', None)
        return Branch.objects.filter(original_file__room__slug=room_slug)


class UploadedFileVersionList(generics.ListAPIView):
    serializer_class = UploadedFileVersionSerializer

    def get_queryset(self):
        # Get the room slug from the URL parameters
        room_slug = self.kwargs.get('room_slug', None)
        return UploadedFileVersion.objects.filter(uploaded_file__room__slug=room_slug)


class UploadedFileVersionDetail(generics.RetrieveAPIView):
    serializer_class = UploadedFileVersionSerializer

    def get_queryset(self):
        # Get the room slug from the URL parameters
        room_slug = self.kwargs.get('room_slug', None)
        return UploadedFileVersion.objects.filter(uploaded_file__room__slug=room_slug)


class CommitList(generics.ListAPIView):
    serializer_class = CommitSerializer

    def get_queryset(self):
        # Get the room slug from the URL parameters
        room_slug = self.kwargs.get('room_slug', None)
        return Commit.objects.filter(branch__original_file__room__slug=room_slug)


class CommitDetail(generics.RetrieveAPIView):
    serializer_class = CommitSerializer

    def get_queryset(self):
        # Get the room slug from the URL parameters
        room_slug = self.kwargs.get('room_slug', None)
        return Commit.objects.filter(branch__original_file__room__slug=room_slug)


