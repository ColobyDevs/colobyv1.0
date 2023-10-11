Coloby
Introduction

This is a  Collaboration system that allows users to create chat rooms, send and receive messages, manage tasks, upload files, and create branches for collaborative work.
Table of Contents

    Prerequisites
    Installation
    Usage
    API Endpoints
    Views
    Models
    Permissions

Prerequisites

Before you can use this application, make sure you have the following installed:

    Python (>=3.7)
    Django
    Django REST framework
    Required dependencies specified in requirements.txt

Installation

    Clone the repository:

    bash

git clone https://github.com/ColobyDevs/Colobyv1.0.git

Install the required dependencies:

bash

pip install -r requirements.txt

Run the Django development server:

bash

    python manage.py runserver

    Access the application in your web browser at http://localhost:8000.

Usage
Creating Chat Rooms

    Use the "Create Room" feature to create new chat rooms.
    Rooms can be public or private.

Joining Chat Rooms

    Use the "Join Room" feature to join an existing chat room.

Sending and Receiving Messages

    Send messages within chat rooms.
    View messages in real-time.

Managing Tasks

    Create tasks in chat rooms.
    Update and delete tasks as needed.

Uploading Files

    Upload files to chat rooms.
    Download and manage files.

Branches

    Create branches for collaborative work on files.
    Merge branches to consolidate changes.

API Endpoints
Messages

    POST /api/chat/send/<room_slug>/ - Send a message to a chat room.
    GET /api/chat/get/<room_slug>/ - Get messages from a chat room.

Tasks

    GET /room/<slug>/tasks/ - Get a list of tasks in a room.
    POST /room/<slug>/tasks/ - Create a new task in a room.
    GET /room/tasks/<task_id>/ - Retrieve a specific task.
    PUT /room/tasks/<task_id>/ - Update a task.
    DELETE /room/tasks/<task_id>/ - Delete a task.

Comments

    POST /room/tasks/<task_id>/comments/ - Create a new comment on a task.
    GET /room/comments/<comment_id>/ - Retrieve a specific comment.
    PUT /room/comments/<comment_id>/ - Update a comment.
    DELETE /room/comments/<comment_id>/ - Delete a comment.

Files

    POST /chat/upload/<room_slug>/ - Upload a file to a chat room.
    GET /chat/list/<room_slug>/ - List files in a chat room.
    GET /chat/download/<room_slug>/<file_id>/ - Download a file from a chat room.

Branches

    GET /api/branches/ - List all branches.
    POST /api/branches/ - Create a new branch.
    GET /api/branches/<branch_id>/ - Retrieve a specific branch.
    PUT /api/branches/<branch_id>/ - Update a branch.
    DELETE /api/branches/<branch_id>/ - Delete a branch.

Views

    index: Main chat room view.
    public_chat: Public chat room view.
    room_create: Create a new chat room.
    room_join: Join an existing chat room.
    upload_file: Upload a file to a chat room.
    file_download: Download a file from a chat room.
    file_access_log: View the access log for a file.
    ...

Models
Room

    Attributes: name, slug, users, is_private, created_by

Message

    Attributes: room, user, message, media, created_at

Task

    Attributes: room, title, description, completed, due_date, assigned_to, created_at

Comment

    Attributes: task, user, text, created_at

UploadedFile

    Attributes: file, object_id, content, room, uploaded_at, uploaded_by, description, access_permissions, file_size

Branch

    Attributes: original_file, created_by, created_at, changes, description

FileAccessLog

    Attributes: file, accessed_by, accessed_at

Permissions

    Public rooms are open to all users.
    Private rooms are accessible only to invited users.
    Branch merging is controlled by access permissions.