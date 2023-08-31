from django import forms
from .models import Task, Comment, Message

class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ['title', 'description', 'due_date', 'assigned_to', 'completed']
        widgets = {
            'due_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }

class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['text']


# class MessageForm(forms.ModelForm):
#     class Meta:
#         model = Message
#         fields = ['message', 'media']