from django.db import models
from django.db.models.query import QuerySet

# Create your models here.
from django.utils import timezone
import uuid
from django.contrib.auth.models import User
# import shortuuid
from django.contrib.auth import get_user_model
from accounts.models import CustomUser
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
import datetime


User = get_user_model()

class SoftDeletionManager(models.Manager):
    """
    A custom manager for models that support soft deletion. This manager filters out
    objects that have a non-null deleted_at field.
    """
    def __init__(self, *args, **kwargs):
        super(SoftDeletionManager, self).__init__(*args, **kwargs)

    def get_queryself(self):
        return super(SoftDeletionManager, self).get_queryset().filter(deleted_at__isnull=True)
    
    def with_deleted(self):
        return super(SoftDeletionManager, self).get_queryset()
    
class BaseModel(models.Model):
    """
    An abstract base model that includes the deleted_at field and the SoftDeletionManager.
    This class will not be created as its own database table but will be inherited by other models
    via Meta class.
    """
    deleted_at = models.DateTimeField(null=True, blank=True)
    objects = SoftDeletionManager()

    class Meta:
        abstract = True

    def delete(self, *args, **kwargs):
        """
        Soft deletes the object by setting the deleted_at field to the current timestamp.
        """
        self.deleted_at = datetime.datetime.now()
        self.save()

    def restore(self):
        """
        Restores a soft-deleted object by setting the deleted_at field to null.
        """
        self.deleted_at = None
        self.save()

class Room(BaseModel):
    name = models.CharField(max_length=128)
    slug = models.SlugField(unique=True)
    users = models.ManyToManyField(CustomUser)
    is_private = models.BooleanField(default=False)
    created_by = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="created_rooms", null=True, blank=True)
    
    def __str__(self):
        return self.name


class Message(BaseModel):
    room = models.ForeignKey(Room, on_delete=models.CASCADE)
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    message = models.TextField(blank=True, null=True, default=None)
    media = models.FileField(upload_to='media', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.room.name} - {self.user.username}: {self.message}"


class Task(BaseModel):
    room = models.ForeignKey(Room, on_delete=models.RESTRICT)
    # RESTRICT will delete the task if its parent is deleted
    title = models.CharField(max_length=100)
    description = models.TextField()
    completed = models.BooleanField(default=False)
    due_date = models.DateTimeField()
    assigned_to = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title
    

class Comment(BaseModel):
    task = models.ForeignKey(Task, on_delete=models.CASCADE)
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Comment by {self.user.username} on {self.task.title}"


class UploadedFile(BaseModel):
    file = models.FileField(upload_to='uploads/')
    object_id = models.PositiveIntegerField(null=True, blank=True, default=None)
    room = models.ForeignKey(Room, on_delete=models.CASCADE)  # Add this foreign key to Room
    uploaded_at = models.DateTimeField(auto_now_add=True)
    uploaded_by = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    description = models.TextField(blank=True)
    access_permissions = models.ManyToManyField(CustomUser, related_name="accessible_files", blank=True)
    file_size = models.PositiveIntegerField(null=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.file_size and self.file:
            self.file_size = self.file.size
        super().save(*args, **kwargs)

    def __str__(self):
        return self.file.name


class FileAccessLog(BaseModel):
    file = models.ForeignKey(UploadedFile, on_delete=models.CASCADE)
    accessed_by = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    accessed_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.accessed_by.username} accessed {self.file.name} at {self.accessed_at} in {self.room.name}"
