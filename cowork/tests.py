from django.test import TestCase
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from .models import Room, Message
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
        # print("Response Content:", response.content)
        # print("Response Headers:", response.headers)

        self.assertEqual(response.status_code, 201)  # Checks if the message was sent successfully

    def test_get_messages(self):
        # User log in
        self.client.login(username='testuser', password='testpassword')

        url = reverse('get_message', kwargs={'room_slug': 'test-room'})
        print("Generated URL for get_message:", url)

        # Get messages
        response = self.client.get(url)
        # print("Response Content:", response.content)
        # print("Response Headers:", response.headers)

        self.assertEqual(response.status_code, 200)  # Checks if messages were retrieved successfully

    def test_authenticated_user_can_send_message(self):
        # User log in
        self.client.login(username='testuser', password='testpassword')

        # Send a message
        url = reverse('send_message', kwargs={'room_slug': 'test-room'})
        data = {
            'message': 'Hello world!',
            'user': self.user.pk,
            'room': self.room.pk
        }
        response = self.client.post(url, data)
        # print("Response Content:", response.content)
        # print("Response Headers:", response.headers)

        self.assertEqual(response.status_code, 201)  # Checks if the message was sent successfully

    def test_unauthenticated_user_cannot_send_message(self):
        url = reverse('send_message', kwargs={'room_slug': 'test-room'})

        data = {
            'message': 'Hello world!',
            'user': self.user.pk,
            'room': self.room.pk
        }

        # Sends a POST request to send the message without logging in
        response = self.client.post(url, data)
        # print("Response Content:", response.content)
        # print("Response Headers:", response.headers)

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
        # print("Response Content:", response.content)
        # print("Response Headers:", response.headers)

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
        # print("Response Content:", response.content)
        # print("Response Headers:", response.headers)

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
        # print("Response Content:", response.content)
        # print("Response Headers:", response.headers)

        self.assertEqual(response.status_code, 200)  # Checks if the user was able to join the private room

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
        # print("Response Content:", response.content)
        # print("Response Headers:", response.headers)

        self.assertEqual(response.status_code, 200)  # Checks if the user was able to join the public room
