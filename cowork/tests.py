from django.test import TestCase
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from .models import Room
from django.urls import reverse


User = get_user_model()

class ChatAPITests(TestCase):
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
