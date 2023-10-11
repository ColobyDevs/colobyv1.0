from rest_framework import serializers
from allauth.account.models import EmailAddress
from accounts.models import CustomUser

from cowork.models import Task, Comment, Message, UploadedFile, Branch

from cowork.models import Task, Comment, Message, UploadedFile, Room

from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model


User = get_user_model()


class UserRegistrationSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ("username", 'email', 'password')

    def create(self, validated_data):
        user = CustomUser.objects.create_user(
            username=validated_data["username"],
            email=validated_data['email'],
            password=validated_data['password']
        )
        EmailAddress.objects.create(user=user, email=user.email, primary=True, verified=True)
        return user

class SignInSerializer(serializers.Serializer):
    """
    Serializer for signing in a user
    """
    
    email = serializers.CharField(write_only=True)
    password = serializers.CharField(write_only=True)
    def validate(self, attrs: dict):
        """
        This is for validating credentials for signing in
        """
        error_messages = {
             "error-mssg-1": {
                "credential_error": "Please recheck the credentials provided."
            },
        }
        
        user = User.objects.filter(email=attrs["email"]).first()
        if user:
            if user.check_password(attrs["password"]):
                return user
            else: # This raises error if the password provided is wrong
                raise serializers.ValidationError(error_messages["error-mssg-1"])
        else: # This raises error if the user doesn't exist
            raise serializers.ValidationError(error_messages["error-mssg-1"])
        
    def to_representation(self, user):
        username =  User.objects.get(email=user).username
        refresh = RefreshToken.for_user(user)
        return {"Info": f"Welcome {username}", "access_token": str(refresh.access_token)}
    
class CustomUserSerializer(serializers.ModelSerializer):
    class Meta:
        fields = ("username", "email", "password")
    
class RoomSerializer(serializers.ModelSerializer):
    users = CustomUserSerializer(many=True)
    created_by = CustomUserSerializer()
    class Meta:
        model = Room
        fields = "__all__"

class SendMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['room'].required = True
        self.fields['user'].required = True
        self.fields['message'].required = True

class ReceiveMessageSerializer(serializers.ModelSerializer):
    user = serializers.ReadOnlyField(source="user.username")

    class Meta:
        model = Message
        fields = ["user", "message", "created_at"]


class TaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = '__all__'


class CommentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        fields = '__all__'


class UploadedFileSerializer(serializers.ModelSerializer):
    owner = serializers.ReadOnlyField(source="uploaded_by.username")
    access_permissions = serializers.StringRelatedField(many=True)
    class Meta:
        model = UploadedFile
        fields = ["file", "description", "owner", "access_permissions", "file_size"]


class BranchSerializer(serializers.ModelSerializer):
    class Meta:
        model = Branch
        fields = ['original_file', 'content', 'description']