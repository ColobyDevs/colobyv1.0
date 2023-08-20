from django.db import models
from accounts.models import User


class Room(models.Model):
    name = models.CharField(max_length=128)
    slug = models.SlugField(unique=True)
    users = models.ManyToManyField(User)

    def __str__(self):
        return self.name


class Message(models.Model):
    room = models.ForeignKey(Room, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.TextField()
    media = models.FileField(upload_to='media', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return (self.room.name + " - " + str(self.user.username) + " : " + str(self.message))


class Task(models.Model):
    room = models.ForeignKey(Room, on_delete=models.RESTRICT)
    # RESTRICT will delete the task if its parent is deleted
    title = models.CharField(max_length=100)
    description = models.TextField()
    completed = models.BooleanField(default=False)
    due_date = models.DateTimeField()
    assigned_to = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title
    

class Comment(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Comment by {self.user.username} on {self.task.title}"





class UploadedFile(models.Model):
    file = models.FileField(upload_to='uploads/')
    room = models.ForeignKey(Room, on_delete=models.CASCADE)  # Add this foreign key to Room
    uploaded_at = models.DateTimeField(auto_now_add=True)
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.file.name


class FileAccessLog(models.Model):
    file = models.ForeignKey(UploadedFile, on_delete=models.CASCADE)
    accessed_by = models.ForeignKey(User, on_delete=models.CASCADE)
    accessed_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.accessed_by.username} accessed {self.file.name} at {self.accessed_at} in {self.room.name}"
