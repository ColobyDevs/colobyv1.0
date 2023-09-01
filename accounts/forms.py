from accounts.models import CustomUser
from django.contrib.auth.forms import UserCreationForm

class UserRegisterForm(UserCreationForm):

    class Meta:
        model= CustomUser
        fields = ['username', 'password1', 'password2']
