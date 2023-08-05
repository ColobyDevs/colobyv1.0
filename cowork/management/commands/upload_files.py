import os
from django.core.management.base import BaseCommand
from django.core.files import File
# from django.contrib.auth.models import User
from accounts.models import User
from cowork.models import UploadedFile, Room
from django.core.management import execute_from_command_line



class Command(BaseCommand):
    help = 'Upload files or folders from the command-line'

    def add_arguments(self, parser):
        parser.add_argument('username', help='Username of the user uploading the files')
        parser.add_argument('room_slug', help='Slug of the room to which the files will be uploaded')
        parser.add_argument('paths', nargs='+', help='List of file or folder paths to upload')

    def handle(self, *args, **kwargs):
        username = kwargs['username']
        room_slug = kwargs['room_slug']  # Get the room slug
        paths = kwargs['paths']
        user = User.objects.get(username=username)
        room = Room.objects.get(slug=room_slug)  # Get the Room object based on the slug

        for path in paths:
            if os.path.exists(path):
                if os.path.isfile(path):
                    self.upload_file(user, room, path)  # Pass the room object to upload_file method
                elif os.path.isdir(path):
                    self.upload_folder(user, room, path)  # Pass the room object to upload_folder method
                else:
                    self.stdout.write(self.style.WARNING(f'Invalid path: {path}'))
            else:
                self.stdout.write(self.style.WARNING(f'Path not found: {path}'))

    def upload_file(self, user, room, file_path):
        with open(file_path, 'rb') as file:
            # Create a Django UploadedFile object from the raw file object
            django_file = File(file, name=os.path.basename(file_path))

            # Create the UploadedFile instance in the database
            uploaded_file_instance = UploadedFile.objects.create(
                file=django_file,
                room=room,  # Set the room for the UploadedFile
                uploaded_by=user,
                description="Your optional description here"  # You can add a description if needed
            )

        self.stdout.write(self.style.SUCCESS(f'Successfully uploaded file: {file_path}'))

    def upload_folder(self, user, room, folder_path):
        for root, _, files in os.walk(folder_path):
            for file_name in files:
                file_path = os.path.join(root, file_name)
                self.upload_file(user, room, file_path)  # Pass the room object to upload_file method
