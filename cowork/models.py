from django.db import models

# Create your models here.
from django.utils import timezone
import uuid
from django.contrib.auth.models import User
import shortuuid
from django.contrib.auth import get_user_model

User = get_user_model()


class Project(models.Model):
    id = models.UUIDField(primary_key = True, default=uuid.uuid4, editable=False)
    users = models.ManyToManyField(User)
    name = models.CharField(max_length=40, unique=True)
    admin = models.ForeignKey(User, on_delete= models.CASCADE, related_name='admins')
    token = models.CharField(max_length=6, unique=True, default=shortuuid.ShortUUID().random)

    def __str__(self):
        return self.name + ' (' + self.admin.username + ')'


    # def save(
    #       self, force_insert=False, force_update=False,
    #        using=None, first_time=False):
    #   if not first_time:
    #        self.users.add(self)
    #   super().save()

    def get_users_names(self):
        for user in self.users.all():
            yield user.username

    def get_channels(self):
        channels = self.channels.all()
        return channels

class Task(models.Model):
    title = models.CharField(max_length=100)
    description = models.TextField()
    due_date = models.DateField()
    assigned_to = models.ForeignKey(User, on_delete=models.CASCADE)
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    completed = models.BooleanField(default=False)

    def __str__(self):
        return self.title

