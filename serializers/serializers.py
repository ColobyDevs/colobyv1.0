from django.contrib.auth import authenticate
from rest_framework import serializers
from allauth.account.models import EmailAddress
from accounts.models import CustomUser
from django.contrib.auth.hashers import check_password

from cowork.models import (
    Room, Task, Comment,
    Message, UploadedFile,
    Branch, UserNote, FeatureRequest, Commit, UploadedFileVersion)

from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model


User = get_user_model()


class UserRegistrationSerializer(serializers.ModelSerializer):
    """
        Serializer is for creating a new user
    """
    password = serializers.CharField(min_length=8, write_only=True)

    class Meta:
        model = CustomUser
        fields = ('email', 'password', 'first_name', 'username')

    # Add any extra fields you want to include in the registration form.
    extra_fields = ['first_name', 'username']

    def create(self, validated_data):
        user = CustomUser.objects.create_user(**validated_data)
        return user 

class SignInSerializer(serializers.Serializer):
    """
    Serializer for signing in
    """
    
    email = serializers.CharField(required=True)
    password = serializers.CharField(required=True)

    def validate(self, attrs: dict):
        """
        This is for validating credentiials for signing in
        """

        user = User.objects.filter(email=attrs["email"]).first()
        if (user is None):
            raise serializers.ValidationError({
                "sucess": "false",
                "message": "user doesn't exist"
            })
    
        elif (user and user.check_password(attrs["password"])):
            return user
        
        else:
            raise serializers.ValidationError({
                "sucess": "false",
                "message": "Invalid credentials"
            })

    
    def to_representation(self, instance):
        user = User.objects.get(email=instance.email)
        refresh = RefreshToken.for_user(instance)
        return {
            "success": ["true"],
            "refresh_token":str(refresh), 
            "access_token": str(refresh.access_token),
	        "user_id": user.id
            }


class ChangePasswordSerializer(serializers.Serializer):
    """This serializer is for changing a user's password"""

    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, min_length=8)
    confirm_new_password = serializers.CharField(write_only=True, min_length=8)

    def validate(self, attrs):
        user = self.context["request"].user
        
        if check_password(attrs["old_password"], user.password) is False:
            raise serializers.ValidationError({
                            "old_password":"Please recheck the old password"
                            })
    
        elif attrs["new_password"] != attrs["confirm_new_password"]:
            raise serializers.ValidationError({
                "confirm_password":"Please confirm the new password"
                })
        
        return attrs
    
    
    
    def update(self, instance, validated_data):
        return super().update(instance, validated_data)

class CustomUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ("username", "email", "password")


class RoomSerializer(serializers.ModelSerializer):
    users = serializers.SerializerMethodField()
    created_by = serializers.SerializerMethodField()

    class Meta:
        model = Room
        fields = "__all__"

    def get_users(self, room):
        return room.users.values_list('username', flat=True)

    def get_created_by(self, room):
        return room.created_by.username if room.created_by else None

class UserNoteSerializer(serializers.Serializer):
    class Meta:
        model = UserNote
        fields = "__all__"


class FeatureRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = FeatureRequest
        fields = '__all__'
        read_only_fields = ('room', 'user')


class SendMessageSerializer(serializers.ModelSerializer):
    media_file = serializers.FileField(allow_empty_file=True, required=False)
    class Meta:
        model = Message
        fields = "__all__"

    def create(self, validated_data):
        media_file = validated_data.pop("media_file", None)
        message = Message.objects.create(**validated_data)

        if media_file:
            message.media = media_file
            message.save()

        return message



class ReceiveMessageSerializer(serializers.ModelSerializer):
    user = serializers.ReadOnlyField(source="user.username")

    class Meta:
        model = Message
        fields = ["user", "message", "media", "created_at"]


class TaskSerializer(serializers.ModelSerializer):
    assigned_to = serializers.SlugRelatedField(
        slug_field='username',
        queryset=CustomUser.objects.all(),
    )
    due_date = serializers.DateField(format='%Y-%m-%d') 

    class Meta:
        model = Task
        fields = '__all__'
        read_only_fields = ['room']

    def validate_assigned_to(self, value):
        # Access the room and creator from the context
        room = self.context['room']
        creator = room.created_by

        # Check if the assigned user is a member of the room (excluding the creator)
        if not (room.users.filter(id=value.id).exists() or value == creator):
            raise serializers.ValidationError("The assigned user must be a member of the room or the room creator.")

        return value



class CommentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        fields = '__all__'

class UploadedFileSerializer(serializers.ModelSerializer):
    owner = serializers.ReadOnlyField(source="uploaded_by.username")
    access_permissions = serializers.StringRelatedField(many=True)

    class Meta:
        model = UploadedFile
        fields = ["file", "description", "owner",
                  "access_permissions", "file_size", "room_id"]
        read_only_fields = ['room']



class BranchSerializer(serializers.ModelSerializer):
    class Meta:
        model = Branch
        fields = ['original_file', 'content', 'description']


        
class UploadedFileVersionSerializer(serializers.ModelSerializer):
    class Meta:
        model = UploadedFileVersion
        fields = ["file", "description", "file_size"]

class CommitSerializer(serializers.ModelSerializer):
    class Meta:
        model = Commit
        fields = ['uploader', 'timestamp', 'description']

class UpdateUserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
        'first_name',
        'email',
        'last_name',
        'username'
        ]

    def validate(self, attrs):
        return super().validate(attrs)
    
