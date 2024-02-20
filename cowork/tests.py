from django.test import TestCase
from rest_framework.test import APIClient, APITestCase
from rest_framework import status
from rest_framework.authtoken.models import Token
from django.contrib.auth import get_user_model
from .models import Room, UploadedFile, Message, Task, Notification
from serializers.serializers import TaskSerializer 
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from django.conf import settings
from datetime import timezone, datetime
import tempfile
import shutil


User = get_user_model()
@override_settings(MEDIA_ROOT=tempfile.mkdtemp(prefix="media"))
class MessageAPITests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword'
        )
        self.token, created = Token.objects.get_or_create(user=self.user)
        self.room = Room.objects.create(
            name='Test Room',
            slug='test-room',
            is_private=False
        )

    def authenticate_client(self):
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token.key}')
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        print(self.token.key)


    # def test_send_message(self):
    #     self.authenticate_client()
    #     url = reverse('send-message', kwargs={'room_slug': 'test-room'})
    #     data = {
    #         'message_text': 'Hello world!',
    #     }
    #     response = self.client.post(url, data)
    #     print(response.status_code)
    #     print(response.content)
    #     self.assertEqual(response.status_code, 201)
    #     self.assertTrue(Message.objects.filter(message_text="Hello world!").exists())

    # def test_send_with_media(self):
    #     self.authenticate_client()
    #     self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token.key}')
    #     url = reverse('send-message', kwargs={'room_slug': 'test-room'})
    #     with tempfile.NamedTemporaryFile(delete=False) as temp_file:
    #         temp_file.write(b'This is the content of the test file.')

    #     with open(temp_file.name, 'rb') as media_file:
    #         data = {
    #             'alt_text': 'Test this pic!',
    #             'media_file': media_file
    #         }
    #         response = self.client.post(url, data, format='multipart')
    #         print(response.status_code)
    #         print(response.content)
    #         self.assertEqual(response.status_code, 201)

    # def test_get_messages(self):
    #     self.authenticate_client()
    #     url = reverse('get-message', kwargs={'room_slug': 'test-room'})
    #     response = self.client.get(url)
    #     print(response.status_code)
    #     print(response.content)
    #     self.assertEqual(response.status_code, 200)

    def test_unauthenticated_user_cannot_send_message(self):
        url = reverse('send-message', kwargs={'room_slug': 'test-room'})
        data = {
            'message_text': 'Hello world!',
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 401)


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
class TaskAPITests(TestCase):
    """Tests for Task API."""
    def setUp(self):
        """Setup test user, room, tasks, and authenticated client."""
        self.user = User.objects.create_user(username='testuser', password='testpassword', email='testuser@example.com')

        self.room = Room.objects.create(name='Test Room', slug='test-room')

        current_time = datetime.now(timezone.utc)

        self.task1 = Task.objects.create(title='Task 1', room=self.room, due_date=datetime(
        current_time.year,
        current_time.month,
        current_time.day,
        current_time.hour,
        current_time.minute,
        current_time.second,
        current_time.microsecond,
        ).astimezone(timezone.utc), assigned_to=self.user,)
        self.task2 = Task.objects.create(title='Task 2', room=self.room, due_date=datetime(
        current_time.year,
        current_time.month,
        current_time.day,
        current_time.hour,
        current_time.minute,
        current_time.second,
        current_time.microsecond,
        ).astimezone(timezone.utc), assigned_to=self.user,)

        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
    
    def test_task_list_create_view(self):
        """
        Tests that calling the API endpoint for creating new tasks:

        - Sends a POST request to the correct URL with appropriate data.
        - Returns a created status code (201).
        - Creates and saves the new task in the database.
        """
        url = reverse('task-list', kwargs={'slug': self.room.slug})

        data = {'title': 'New Task',
                'description': 'Task description',  
                'due_date': '2023-12-21T12:00:00Z', 
                'room': self.room.id,  
                'assigned_to': self.user.id, }

        response = self.client.post(url, data, format='json')
        print(response.content)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertEqual(Task.objects.count(), 3)

    # def test_task_detail(self):
    #     """
    #     Tests that the API endpoint for managing individual tasks:

    #     - Retrieves the existing task information with a GET request.
    #     - Updates the task title with a PUT request (200 status code).
    #     - Verifies the updated title in the database.
    #     - Deletes the task with a DELETE request (204 status code).
    #     - Confirms only one task remains in the database.
    #     """
    #     url = reverse('task-detail', kwargs={'pk': self.task1.pk})

    #     response = self.client.get(url)
    #     print(response.content)
    #     self.assertEqual(response.status_code, status.HTTP_200_OK)

    #     updated_data = {'title': 'Updated Task',
    #                     'description': 'Task description',  
    #                     'due_date': '2023-12-21T12:00:00Z', 
    #                     'room': self.room.id,  
    #                     'assigned_to': self.user.id,}
    #     response = self.client.put(url, updated_data, format='json')
    #     print(response.content)
    #     self.assertEqual(response.status_code, status.HTTP_200_OK)

    #     self.task1.refresh_from_db()
    #     self.assertEqual(self.task1.title, 'Updated Task')

    #     print("Task count before deletion:", Task.objects.count())
    #     response = self.client.delete(url)
    #     print("Task count after deletion:", Task.objects.count())
    #     self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    #     self.assertEqual(Task.objects.count(), 1)

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

    # def test_upload_file(self):
    #     """Tests that a logged-in user can upload a file to a room."""
    #     self.client.login(username='testuser', password='testpassword')
    #     url = reverse('upload-file', kwargs={'room_slug': 'test-room'})

    #     test_file = SimpleUploadedFile("test_file.txt", b"file_content")

    #     data = {
    #         'file': test_file,
    #         'description': 'Test file description',
    #     }

    #     response = self.client.post(url, data, format='multipart')
    #     self.assertEqual(response.status_code, 200)

    def test_file_list(self):
        """Tests that a logged-in user can get/view a list of files uploaded to a room."""
        self.client.login(username='testuser', password='testpassword')
        url =  reverse('file-list', kwargs={'room_slug': 'test-room'})

        response = self.client.get(url)
        self.assertIn('application/json', response['Content-Type'])
        self.assertEqual(response.status_code, 200)

    def test_file_download(self):
        """Tests that a logged-in user can download a file from a room."""
        self.client.login(username='testuser', password='testpassword')
        url = reverse('file-download', kwargs={'room_slug': 'test-room', 'file_id': 1})

        response = self.client.get(url)
        response['Content-Type'] = 'application/octet-stream'
        self.assertEqual(response.status_code, 200)

    # def test_edit_uploaded_file(self):
    #     """Tests that a logged-in user can edit a file from a room."""
    #     self.client.login(username='testuser', password='testpassword')
    #     url = reverse('edit-uploaded-file', args=[self.uploaded_file.id])

    #     response = self.client.get(url)

    #     self.assertEqual(response.status_code, status.HTTP_200_OK)
    #     self.assertEqual(response.json(), {"status": "You are editing this file now"})

    #     edited_desc = "Edited Description 1 2 3"
    #     response = self.client.post(url, {'description': edited_desc})

    #     self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    #     self.assertIn("error", response.json())

    #     updated_file = UploadedFile.objects.get(id=self.uploaded_file.id)
    #     self.assertNotEqual(updated_file.description, edited_desc)

# @override_settings(MEDIA_ROOT=tempfile.mkdtemp(prefix="media"))
# class NotificationAPITests(TestCase):
#     """Test cases for the Notification API endpoints.

#     These tests cover retrieving lists and details of notifications, as well as marking them as read.
#     """
#     def setUp(self):
#         """
#         Creates a user, a room, and several notifications for testing purposes.
#         """
#         self.user = User.objects.create_user(username='testuser', email='test@example.com', password='password')

#         self.room = Room.objects.create(name='Test Room', slug='test-room')

#         # Some notifications
#         self.notification1 = Notification.objects.create(user=self.user, message="Notification 1")
#         self.notification2 = Notification.objects.create(user=self.user, message="Notification 2")
#         self.notification3 = Notification.objects.create(user=self.user, message="Notification 3")

#     def test_notification_list(self):
#         """
#         Tests retrieving a list of notifications for the authenticated user.

#         - Authenticates a user with the client.
#         - Sends a GET request to the notification list endpoint.
#         - Asserts that the response status code is 200 (OK).
#         - Asserts that the response data contains 3 notifications.
#         """
#         client = APIClient()
#         client.force_authenticate(user=self.user)
#         url = reverse('notification-list')
#         response = client.get(url)
#         self.assertEqual(response.status_code, status.HTTP_200_OK)
#         self.assertEqual(len(response.data), 3)

#     def test_notification_detail(self):
#         """
#         Tests retrieving a single notification by its ID.

#         - Authenticates a user with the client.
#         - Sends a GET request to the notification detail endpoint for a specific notification ID.
#         - Asserts that the response status code is 200 (OK).
#         - Asserts that the response data contains the expected notification message.
#         """
#         client = APIClient()
#         client.force_authenticate(user=self.user)
#         url = reverse('notification-detail', args=[self.notification1.id])
#         response = client.get(url)
#         self.assertEqual(response.status_code, status.HTTP_200_OK)
#         self.assertEqual(response.data['message'], self.notification1.message)

#     def test_mark_notification_as_read(self):
#         """
#         Tests marking a notification as read.

#         - Authenticates a user with the client.
#         - Sends a POST request to the mark-notification-as-read endpoint with a notification ID.
#         - Asserts that the response status code is 200 (OK).
#         - Refreshes the notification object from the database.
#         - Asserts that the notification is now marked as read.
#         """
#         client = APIClient()
#         client.force_authenticate(user=self.user)
#         url = reverse('mark-notification-as-read', args=[self.notification1.id])
#         response = client.post(url)
#         self.assertEqual(response.status_code, status.HTTP_200_OK)
#         self.notification1.refresh_from_db()
#         self.assertTrue(self.notification1.read)


    @classmethod
    def tearDownClass(cls):
        """Removes the temporary media file directory after testing is concluded."""
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()
