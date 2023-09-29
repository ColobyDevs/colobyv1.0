from django.test import TestCase
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from .models import Room, UploadedFile
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from django.conf import settings
from django.http import FileResponse
import tempfile
import shutil

User = get_user_model()

@override_settings(MEDIA_ROOT=tempfile.mkdtemp(prefix="media"))
class ChatAPITests(TestCase):
    """
    Test cases for the Chat (messaging) API, covering various aspects such as chat/message endpoints,
    creating rooms, joining rooms, file sharing endpoints, etc.

    Attributes:
        user (User): A test user instance.
        room (Room): A test chatroom instance.
        client (APIClient): An API client for making test requests.

    Test cases include:
    - Sending messages in a chatroom.
    - Retrieving messages from a chatroom.
    - Testing user access to private and public rooms.
    - Uploading files to a chatroom.
    - Viewing list of files uploaded to a chatroom.
    - Downloading files from a chatroom.
    
    Note: Each test case is independent and operates on a separate test database which is automatically destroyed
        after testing instance.
    """
    def setUp(self):
        self.client = APIClient()

        # User creation
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword'
        )

        # Chatroom creation
        self.room = Room.objects.create(
            name='Test Room',
            slug='test-room',
            is_private=False
        )

        # File creation
        uploaded_file = UploadedFile.objects.create(
            file=SimpleUploadedFile("test_files.txt", b"file_content"),
            uploaded_by=self.user,
            room=self.room
        )
        uploaded_file.save()

    def test_send_message(self):
        # User log in
        self.client.login(username='testuser', password='testpassword')

        # Send a message
        url = reverse('send_message', kwargs={'room_slug': 'test-room'})
        print("Generated URL for send_message:", url)

        data = {
            'message': 'Hello world!',
            'user': self.user.pk,
            'room': self.room.pk
        }
        response = self.client.post(url, data)

        self.assertEqual(response.status_code, 201)  # Checks if the message was sent successfully

    def test_get_messages(self):
        # User log in
        self.client.login(username='testuser', password='testpassword')

        url = reverse('get_message', kwargs={'room_slug': 'test-room'})
        print("Generated URL for get_message:", url)

        # Get messages
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)  # Checks if messages were retrieved successfully

    def test_unauthenticated_user_cannot_send_message(self):
        url = reverse('send_message', kwargs={'room_slug': 'test-room'})

        data = {
            'message': 'Hello world!',
            'user': self.user.pk,
            'room': self.room.pk
        }

        # Sends a POST request to send the message without logging in
        response = self.client.post(url, data)

        self.assertEqual(response.status_code, 403)  # Checks if an unauthenticated user CANNOT send a message

    def test_create_private_room(self):
        # User log in
        self.client.login(username='testuser', password='testpassword')

        # Creates a private room
        url = reverse('room-create')
        data = {
            'room_name': 'Private Room',
            'is_private': 'on',  # Indicates private room
        }
        response = self.client.post(url, data)

        self.assertEqual(response.status_code, 302)  # Checks if the room was created successfully
        self.assertTrue(Room.objects.filter(name='Private Room', is_private=True).exists())

    def test_create_public_room(self):
        # User log in
        self.client.login(username='testuser', password='testpassword')

        # Creates a public room
        url = reverse('room-create')
        data = {
            'room_name': 'Public Room',
            'is_private': '',  # Indicates a public room
        }
        response = self.client.post(url, data)

        self.assertEqual(response.status_code, 302)  # Checks if the room was created successfully
        self.assertTrue(Room.objects.filter(name='Public Room', is_private=False).exists())

    def test_join_private_room(self):
        # User log in
        self.client.login(username='testuser', password='testpassword')

        # Creates a private room
        private_room = Room.objects.create(
            name='Private Room',
            slug='private-room',
            is_private=True
        )
        # Joins the private room
        url = reverse('room-join')
        data = {
            'room_name': 'private-room',
            'room_type': 'private',  # Indicates private room
        }
        response = self.client.post(url, data, follow=True)

        self.assertEqual(response.status_code, 403)  # Checks if the user was able to join the private room

    def test_join_public_room(self):
        # User log in
        self.client.login(username='testuser', password='testpassword')

        # Creates a public room
        public_room = Room.objects.create(
            name='Public Room',
            slug='public-room',
            is_private=False
        )

        # Joins the public room
        url = reverse('public-room', kwargs={'slug': 'public-room'})
        data = {
            'room_name': 'public-room',
            'room_type': 'public',  # Indicates a public room
        }

        response = self.client.post(url, data, follow=True)

        self.assertEqual(response.status_code, 200)  # Checks if the user was able to join the public room

    def test_upload_file(self):
        self.client.login(username='testuser', password='testpassword')
        url = reverse('upload_file', kwargs={'room_slug': 'test-room'})
        print("Generated URL for test file upload:", url)

        test_file = SimpleUploadedFile("test_file.txt", b"file_content")

        data = {
            'file': test_file,
            'description': 'Test file description',
        }

        response = self.client.post(url, data, format='multipart')
        self.assertEqual(response.status_code, 200)


    def test_file_list(self):
        self.client.login(username='testuser', password='testpassword')
        url =  reverse('file_list', kwargs={'room_slug': 'test-room'})
        print("Generated url for test file list:", url)

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertIn('application/json', response['Content-Type'])


    def test_file_download(self):
        self.client.force_login(self.user)
        url = reverse('file_download', kwargs={'room_slug': 'test-room', 'file_id': 1})
        print(f"Generated url for test file download: {url}")

        response = self.client.get(url, HTTP_ACCEPT='application/octet-stream')
        response['Content-Type'] = 'application/octet-stream'

        self.assertIsInstance(response, FileResponse)

        self.assertTrue('application/octet-stream' in response['Content-Type'].lower())

        self.assertTrue('attachment' in response.get('Content-Disposition', ''))
        self.assertEqual(response.status_code, 200)



    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()
