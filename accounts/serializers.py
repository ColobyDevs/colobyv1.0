from rest_framework import serializers
from allauth.account.models import EmailAddress
from accounts.models import CustomUser

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
