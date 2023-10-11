from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from .models import Room, UploadedFile
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from django.conf import settings
import tempfile
import shutil
import secrets
import string

User = get_user_model()

@override_settings(MEDIA_ROOT=tempfile.mkdtemp(prefix="media"))
class MessageAPITests(TestCase):
    """Tests for Message API."""
    def setUp(self):
        """Creates a test user and room."""
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword'
        )
        self.room = Room.objects.create(
            name='Test Room',
            slug='test-room',
            is_private=False
        )

    def test_send_message(self):
        """Tests that a logged-in user can send a message to a room."""
        self.client.login(username='testuser', password='testpassword')
        url = reverse('send-message', kwargs={'room_slug': 'test-room'})

        data = {
            'message': 'Hello world!',
            'user': self.user.pk,
            'room': self.room.pk
        }
        response = self.client.post(url, data)

        self.assertEqual(response.status_code, 201)

    def test_get_messages(self):
        """Tests that a logged-in user can get/receive all messages in a room."""
        self.client.login(username='testuser', password='testpassword')
        url = reverse('get-message', kwargs={'room_slug': 'test-room'})

        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)

    def test_unauthenticated_user_cannot_send_message(self):
        """Tests that an unauthenticated user cannot send a message."""
        url = reverse('send-message', kwargs={'room_slug': 'test-room'})

        data = {
            'message': 'Hello world!',
            'user': self.user.pk,
            'room': self.room.pk
        }

        response = self.client.post(url, data)

        self.assertEqual(response.status_code, 403)

@override_settings(MEDIA_ROOT=tempfile.mkdtemp(prefix="media"))
class RoomAPITests(TestCase):
    """Tests for Room API."""
    def setUp(self):
        """Creates a test user and room."""
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword'
        )
        self.room = Room.objects.create(
            name='Test Room',
            slug='test-room',
            is_private=False
        )

    def test_create_private_room(self):
        """Tests that a logged-in user can create a private room."""
        self.client.login(username='testuser', password='testpassword')
        url = reverse('room-create')
        data = {
            'room_name': 'Private Room',
            'is_private': 'on',
        }
        response = self.client.post(url, data)

        self.assertEqual(response.status_code, 302)
        self.assertTrue(Room.objects.filter(name='Private Room', is_private=True).exists())

    def test_create_public_room(self):
        """Tests that a logged-in user can create a public room."""
        self.client.login(username='testuser', password='testpassword')
        url = reverse('room-create')
        data = {
            'room_name': 'Public Room',
            'is_private': '',
        }
        response = self.client.post(url, data)

        self.assertEqual(response.status_code, 302)
        self.assertTrue(Room.objects.filter(name='Public Room', is_private=False).exists())

    def test_join_private_room(self):
        """Tests that a logged-in user cannot join a private room without being invited."""
        self.client.login(username='testuser', password='testpassword')
        private_room = Room.objects.create(
            name='Private Room',
            slug='private-room',
            is_private=True
        )
        url = reverse('room-join')
        data = {
            'room_name': 'private-room',
            'room_type': 'private',
        }
        response = self.client.post(url, data, follow=True)

        self.assertEqual(response.status_code, 403)

    def test_join_public_room(self):
        """Tests that a logged in user can a public room."""
        self.client.login(username='testuser', password='testpassword')
        public_room = Room.objects.create(
            name='Public Room',
            slug='public-room',
            is_private=False
        )
        url = reverse('public-room', kwargs={'slug': 'public-room'})
        data = {
            'room_name': 'public-room',
            'room_type': 'public',
        }

        response = self.client.post(url, data, follow=True)

        self.assertEqual(response.status_code, 200)

    def test_generate_unique_link(self):
        """Tests that a unique link is generated when creating a room."""
        self.client.login(username='testuser', password='testpassword')
        url = reverse('room-create')
        data = {
            'room_name': 'Unique-Link-Room',
            'is_private': '',
        }
        response = self.client.post(url, data)

        self.assertEqual(response.status_code, 302)

        created_room = Room.objects.get(name='Unique-Link-Room')

        self.assertTrue(created_room.unique_link)

@override_settings(MEDIA_ROOT=tempfile.mkdtemp(prefix="media"))
class FileAPITests(TestCase):
    """Tests for File API."""
    def setUp(self):
        """Creates a test user, room and uploaded file."""
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword'
        )
        self.room = Room.objects.create(
            name='Test Room',
            slug='test-room',
            is_private=False
        )
        self.uploaded_file = UploadedFile.objects.create(
            file=SimpleUploadedFile("test_files.txt", b"file_content"),
            uploaded_by=self.user,
            room=self.room,
            description='Test File Description'
        )
        self.uploaded_file.save()

    def test_upload_file(self):
        """Tests that a logged-in user can upload a file to a room."""
        self.client.login(username='testuser', password='testpassword')
        url = reverse('upload-file', kwargs={'room_slug': 'test-room'})

        test_file = SimpleUploadedFile("test_file.txt", b"file_content")

        data = {
            'file': test_file,
            'description': 'Test file description',
        }

        response = self.client.post(url, data, format='multipart')
        self.assertEqual(response.status_code, 200)

    def test_file_list(self):
        """Tests that a logged-in user can get/view a list of files uploaded to a room."""
        self.client.login(username='testuser', password='testpassword')
        url =  reverse('file-list', kwargs={'room_slug': 'test-room'})

        response = self.client.get(url)
        self.assertIn('application/json', response['Content-Type'])
        self.assertEqual(response.status_code, 200)

    def test_file_download(self):
        """Tests that a logged-in user can download a file from a room."""
        self.client.force_login(self.user)
        url = reverse('file-download', kwargs={'room_slug': 'test-room', 'file_id': 1})

        response = self.client.get(url)
        response['Content-Type'] = 'application/octet-stream'
        self.assertEqual(response.status_code, 200)

    def test_edit_uploaded_file(self):
        """Tests that a logged-in user can edit a file from a room."""
        self.client.login(username='testuser', password='testpassword')
        url = reverse('edit-uploaded-file', args=[self.uploaded_file.id])

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json(), {"status": "You are editing this file now"})

        edited_desc = "Edited Description 1 2 3"
        response = self.client.post(url, {'description': edited_desc})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.json())

        updated_file = UploadedFile.objects.get(id=self.uploaded_file.id)
        self.assertNotEqual(updated_file.description, edited_desc)


    @classmethod
    def tearDownClass(cls):
        """Removes the temporary media file directory after testing is concluded."""
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()
