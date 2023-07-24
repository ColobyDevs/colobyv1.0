from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Project
from django.db import IntegrityError
import shortuuid

@login_required
def create_project(request):
    if request.method == 'POST':
        name = request.POST['name']
        admin = request.user
        try:
            new_project = Project.objects.create(name=name, admin=admin)
            new_project.users.add(request.user)
            return render(request, 'cowork/project_token.html', {'project': new_project})
        except IntegrityError:
            # Handle the case when a project with the same name already exists
            return render(request, 'cowork/create_project.html', {'error': 'A project with this name already exists.'})
    return render(request, 'cowork/create_project.html')

@login_required
def join_project(request, project_id):
    project = get_object_or_404(Project, pk=project_id)
    if request.method == 'POST':
        token = request.POST.get('token', '')
        if token == str(project.token):
            project.users.add(request.user)
            return redirect('project_detail', project_id=project.id)
        else:
            return render(request, 'cowork/invalid_token.html')
    return render(request, 'cowork/join_project.html', {'project': project})


@login_required
def project_detail(request, project_id):
    project = get_object_or_404(Project, pk=project_id)
    return render(request, 'cowork/project_details.html', {'project': project})