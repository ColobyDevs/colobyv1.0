from django.contrib.auth.models import AbstractUser
from collections.abc import Iterable
from django.db import models
from django.db.models.query import QuerySet

# Create your models here.
from django.utils import timezone
import uuid
from django.contrib.auth.models import User
# import shortuuid
from django.contrib.auth import get_user_model
from accounts.models import CustomUser
import datetime
from tinymce.models import HTMLField


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
    # deleted_at = models.DateTimeField(null=True, blank=True)
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
    unique_link = models.CharField(
        max_length=50, unique=True, default=uuid.uuid4().hex[:50])
    slug = models.SlugField(unique=True)
    users = models.ManyToManyField(CustomUser)
    is_private = models.BooleanField(default=False)
    created_by = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name="created_rooms",
        null=True,
        blank=True,
        db_column='created_by'  # Set the db_column parameter
    )
    likes = models.ManyToManyField(
        CustomUser, related_name="liked_rooms", blank=True)
    description = models.CharField(max_length=300, blank=True, null=True)

    def save(self, *args, **kwargs):
        if not self.unique_link or Room.objects.filter(unique_link=self.unique_link).exists():
            self.unique_link = uuid.uuid4().hex[:50]
            while Room.objects.filter(unique_link=self.unique_link).exists():
                self.unique_link = uuid.uuid4().hex[:50]
        super(Room, self).save(*args, **kwargs)

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

# A feature where users can create notes to pen ideas down


class UserNote(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=100)
    content = models.TextField()
    last_saved = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

# Feature Request where room memebers can request a feature or something else


class FeatureRequest(models.Model):
    description = models.TextField()
    votes = models.PositiveIntegerField(default=0)
    implemented = models.BooleanField(default=False)
    room = models.ForeignKey(Room, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)


class Task(BaseModel):
    room = models.ForeignKey(Room, on_delete=models.RESTRICT)
    # RESTRICT will delete the task if its parent is deleted
    title = models.CharField(max_length=100)
    description = models.TextField()
    completed = models.BooleanField(default=False)
    due_date = models.DateField()
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
    object_id = models.PositiveIntegerField(
        null=True, blank=True, default=None)
    content = HTMLField(default="<p>You put something here...</p>")
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name="uploaded_files", default=None)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    uploaded_by = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    description = models.TextField(blank=True)
    access_permissions = models.ManyToManyField(
        CustomUser, related_name="accessible_files", blank=True)
    file_size = models.PositiveIntegerField(null=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.file_size and self.file:
            self.file_size = self.file.size
        super().save(*args, **kwargs)

    def __str__(self):
        return self.file.name


class Branch(BaseModel):
    original_file = models.ForeignKey(UploadedFile, on_delete=models.CASCADE)
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name="uploaded_files_branch", default=None)
    created_by = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    content = HTMLField(default="<p>Your changes go here...</p>")
    description = models.TextField(blank=True)

    def __str__(self):
        return f"Branch of {self.original_file.file.name} by {self.created_by.username}"


class Commit(BaseModel):
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE)
    uploader = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)
    description = models.TextField(blank=True)


class UploadedFileVersion(BaseModel):
    uploaded_file = models.ForeignKey(UploadedFile, on_delete=models.CASCADE)
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name="uploaded_files_version", default=None)
    commit = models.ForeignKey(Commit, on_delete=models.CASCADE)
    file = models.FileField(upload_to='uploads/versions/')
    description = models.TextField(blank=True)
    file_size = models.PositiveIntegerField(null=True, blank=True)
