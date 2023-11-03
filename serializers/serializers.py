from django.contrib.auth import authenticate
from rest_framework import serializers
from allauth.account.models import EmailAddress
from accounts.models import CustomUser

from cowork.models import (
    Room, Task, Comment,
    Message, UploadedFile,
    Branch, UserNote, FeatureRequest)

from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model


User = get_user_model()


class UserRegistrationSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ('email', 'password', 'first_name', 'username')

    # Add any extra fields you want to include in the registration form.
    extra_fields = ['first_name', 'username']

    def create(self, validated_data):
        user = CustomUser.objects.create_user(
            email=validated_data['email'],
            password=validated_data['password'],
            first_name=validated_data.get('first_name'),
            username=validated_data.get('username')
        )
        return user


class SignInSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField()

    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')

        user = authenticate(request=self.context.get(
            'request'), username=email, password=password)

        if user is None:
            raise serializers.ValidationError(
                'Invalid credentials. Please recheck your email and password.')

        attrs['user'] = user
        return attrs


class CustomUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ("username", "email", "password")


class RoomSerializer(serializers.ModelSerializer):
    users = CustomUserSerializer(many=True)
    created_by = CustomUserSerializer()

    class Meta:
        model = Room
        fields = "__all__"


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
        fields = ["file", "description", "owner",
                  "access_permissions", "file_size"]


class BranchSerializer(serializers.ModelSerializer):
    class Meta:
        model = Branch
        fields = ['original_file', 'content', 'description']
