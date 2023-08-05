from .models import UploadedFile, FileAccessLog
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, reverse, redirect, get_object_or_404
from django.utils.text import slugify
import string
import random
from cowork.models import Room
from .models import Task
from .forms import TaskForm


@login_required
def index(request, slug):
    room = Room.objects.get(slug=slug)
    tasks = Task.objects.filter(room=room)
    return render(request, 'chat/room.html', {'name': room.name, 'slug': room.slug, 'tasks': tasks})


@login_required
def room_create(request):
    if request.method == "POST":
        room_name = request.POST["room_name"]
        uid = str(''.join(random.choices(
            string.ascii_letters + string.digits, k=4)))
        room_slug = slugify(room_name + "_" + uid)
        room = Room.objects.create(name=room_name, slug=room_slug)
        return redirect(reverse('chat', kwargs={'slug': room.slug}))
    else:
        return render(request, 'chat/create.html')


@login_required
def room_join(request):
    if request.method == "POST":
        room_name = request.POST["room_name"]
        room = Room.objects.get(slug=room_name)
        return redirect(reverse('chat', kwargs={'slug': room.slug}))
    else:
        return render(request, 'chat/join.html')


@login_required
def create_task(request, slug):
    room = get_object_or_404(Room, slug=slug)

    if request.method == 'POST':
        form = TaskForm(request.POST)
        if form.is_valid():
            task = form.save(commit=False)
            task.room = room
            task.save()
            return redirect('/')
    else:
        form = TaskForm()

    return render(request, 'chat/create_task.html', {'form': form, 'room': room})


@login_required
def update_task(request, slug, task_id):
    room = get_object_or_404(Room, slug=slug)
    task = get_object_or_404(Task, pk=task_id)

    if request.method == 'POST':
        form = TaskForm(request.POST, instance=task)
        if form.is_valid():
            form.save()
            return redirect(reverse('index', kwargs={'slug': room.slug}))
    else:
        form = TaskForm(instance=task)

    return render(request, 'chat/update_task.html', {'form': form, 'room': room, 'task': task})


@login_required
def delete_task(request, slug, task_id):
    room = get_object_or_404(Room, slug=slug)
    task = get_object_or_404(Task, pk=task_id)

    if request.method == 'POST':
        task.delete()
        return redirect(reverse('index', kwargs={'slug': room.slug}))

    return render(request, 'chat/delete_task.html', {'room': room, 'task': task})


@login_required
def upload_file(request, room_slug):
    if request.method == 'POST' and request.FILES.get('file'):
        uploaded_file = request.FILES['file']
        description = request.POST.get('description', '')
        room = get_object_or_404(Room, slug=room_slug)
        uploaded_file_instance = UploadedFile.objects.create(
            file=uploaded_file,
            room=room,
            uploaded_by=request.user,
            description=description
        )
        # You can optionally add a success message here
        return redirect('file_list', room_slug=room_slug)

    return render(request, 'file_manager/upload_file.html')


@login_required
def file_list(request, room_slug):
    room = get_object_or_404(Room, slug=room_slug)
    uploaded_files = UploadedFile.objects.filter(room=room)
    return render(request, 'file_manager/file_list.html', {'room': room, 'uploaded_files': uploaded_files})


@login_required
def file_access_log(request, file_id):
    uploaded_file = get_object_or_404(UploadedFile, id=file_id)
    access_logs = FileAccessLog.objects.filter(file=uploaded_file)
    return render(request, 'file_manager/file_access_log.html', {'uploaded_file': uploaded_file, 'access_logs': access_logs})
