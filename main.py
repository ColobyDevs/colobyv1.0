import argparse
import getpass
import os
import requests
import shutil
import hashlib
import pickle
import json
import time
import openai
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Define the base URL of your Django application
BASE_URL = 'http://127.0.0.1:8000/'

MAX_UPLOAD_RETRIES = 3  # Maximum number of upload retries

# Global variables to keep track of the current working directory, session data, and queued files
current_directory = os.getcwd()
session_data = {
    'email': None,
    'password': None,
}
queued_files = []  # List to store files to be uploaded

# Set REPO_DIR to the current working directory
REPO_DIR = os.getcwd()

# Customizable command configuration
custom_commands = {}  # Dictionary to store user-defined custom commands and handlers

# Load AI configuration from ai_config.json
with open("ai_config.json", "r") as config_file:
    ai_config = json.load(config_file)

# Initialize the OpenAI API client
openai.api_key = ai_config["api_key"]

class MyHandler(FileSystemEventHandler):
    def on_modified(self, event):
        if event.is_directory:
            return
        file_path = event.src_path
        if file_path not in queued_files:
            queued_files.append(file_path)
            print(f"File '{file_path}' added to the upload queue.")

def init_repo():
    """Initialize a new repository."""
    if os.path.exists(REPO_DIR):
        print("Repository already exists. Reinitialized.")
    else:
        os.makedirs(REPO_DIR, exist_ok=True)
        print("Initialized an empty repository in", REPO_DIR)

def create_commit(message, user_data):
    """Create a commit with the specified message and upload it to the room."""
    commit_dir = os.path.join(REPO_DIR, 'commits')
    os.makedirs(commit_dir, exist_ok=True)

    # Simulate adding and tracking files
    tracked_files = [os.path.join(REPO_DIR, 'colup.py'), os.path.join(REPO_DIR, 'file2.txt')]

    # Ensure 'email' is present in the user_data dictionary
    if 'email' not in user_data:
        print("User data does not contain an email.")
        return

    # Create a commit object
    commit_data = {
        'message': message,
        'files': tracked_files,
        'user': user_data['email'],  # Use the 'email' field as the identifier
    }

    # Calculate a unique commit hash based on commit data
    commit_hash = hashlib.sha1(str(commit_data).encode()).hexdigest()

    # Save the commit data to a file
    commit_file = os.path.join(commit_dir, commit_hash + '.json')
    with open(commit_file, 'w') as f:
        f.write(str(commit_data))

    print(f"Committed: {message}")

    # Upload the commit to the specified room
    room_slug = input("Enter the room slug: ")  # Prompt user for room slug
    description = input("Enter a description for the commit: ")  # Prompt user for commit description
    if upload_to_room(room_slug, commit_file, description):
        print(f"Commit '{commit_hash}' uploaded to room '{room_slug}' successfully.")
    else:
        print(f"Failed to upload commit '{commit_hash}' to room '{room_slug}'.")

def authenticate_user(email, password):
    """
    Authenticate the user with the Django backend.
    """
    login_url = BASE_URL + 'api/auth/log-in/'
    credentials = {'email': email, 'password': password}

    try:
        response = requests.post(login_url, data=credentials)
        response.raise_for_status()  # Raise an exception for HTTP errors

        if response.status_code == 200:
            session_data['email'] = email
            session_data['password'] = password
            save_session_data()
            return True
        else:
            print("Authentication failed. Please check your email and password.")
            return False

    except requests.exceptions.RequestException as e:
        print(f"Authentication failed: {e}")
        return False

def check_authentication():
    """
    Check if the user is authenticated by verifying session data.
    """
    if not session_data.get('email') or not session_data.get('password'):
        print("Authentication required. Please log in.")
        login_prompt()  # Prompt the user to log in
        if not session_data.get('email') or not session_data.get('password'):
            print('Login failed. Authentication is required for this operation.')
            return False
    return True

def login_prompt():
    """
    Prompt the user for login credentials and return user data.
    """
    while True:
        email = input('Enter your email: ')
        password = getpass.getpass('Enter your password: ')
        user = authenticate_user(email, password)
        if user:
            user_data = {
                'email': user.email,
                'first_name': user.first_name,
                'user_id': str(user.id),
            }
            session_data['email'] = email
            session_data['password'] = password
            save_session_data()
            print(f'Logged in as {email}.')
            return user_data
        else:
            print('Login failed. Please try again.')

def execute_custom_command(command_name, *args):
    """
    Execute a user-defined custom command.
    """
    if command_name in custom_commands:
        custom_commands[command_name](*args)
    else:
        print(f"Custom command '{command_name}' not found.")

def commit_and_colup(message, description):
    """
    Commit changes and add files to the upload queue.
    """
    if not check_authentication():
        return

    create_commit(message, session_data['email'])
    add_to_queue(REPO_DIR, description)

def upload_to_room(room_slug, file_path, description):
    """
    Upload a file or commit to a specified room with retry logic.
    """
    upload_url = BASE_URL + f'api/v1/chat/upload/{room_slug}/'

    # Check if the room slug is not found
    if not room_slug:
        print("Invalid room. Please provide a valid room slug.")
        return

    for attempt in range(1, MAX_UPLOAD_RETRIES + 1):
        try:
            # Check if the file or commit file exists locally
            if not os.path.exists(file_path):
                print(f"File or commit file '{file_path}' not found.")
                return

            if os.path.isfile(file_path):
                # Prepare the file for uploading
                with open(file_path, 'rb') as file:
                    file_data = file.read()  # Read the file content
                    files = {'file': (os.path.basename(file_path), file_data)}

            # Include description in the request
            data = {'description': description}

            # Perform the file upload
            response = requests.post(upload_url, files=files, data=data,
                                     auth=(session_data['email'], session_data['password']))
            response.raise_for_status()  # Raise an exception for HTTP errors

            if response.status_code == 200:
                print(f"{'Commit' if os.path.isdir(file_path) else 'File'} '{file_path}' uploaded successfully to room '{room_slug}'.")
                break
            else:
                print(f"Failed to upload {'commit' if os.path.isdir(file_path) else 'file'} to room '{room_slug}'.")

        except requests.exceptions.RequestException as e:
            print(f"{'Commit' if os.path.isdir(file_path) else 'File'} upload attempt {attempt} failed: {e}")

def save_session_data():
    """
    Save session data to a file.
    """
    with open('session_data.pkl', 'wb') as f:
        pickle.dump(session_data, f)

def load_session_data():
    """
    Load session data from a file.
    """
    if os.path.exists('session_data.pkl'):
        with open('session_data.pkl', 'rb') as f:
            data = pickle.load(f)
            session_data.update(data)

def change_directory(new_directory):
    """
    Change the current working directory.
    """
    global current_directory
    try:
        os.chdir(new_directory)
        current_directory = os.getcwd()
        print(f"Current directory: {current_directory}")
    except FileNotFoundError:
        print(f"Directory '{new_directory}' not found.")
    except Exception as e:
        print(f"Error changing directory: {e}")

def add_to_queue(file_path, description):
    """
    Add a file or directory to the upload queue.
    """
    queued_files.append((file_path, description))
    print(f"File or directory '{file_path}' added to the upload queue with description: {description}")

def upload_queued_files(room_name, user_data):
    """
    Upload files from the queue to a specified room.
    """
    if not check_authentication():
        print('Login failed.')
        return

    for file_path, description in queued_files:
        upload_to_room(room_name, file_path, description)

def load_custom_commands(config_file):
    """
    Load user-defined custom commands from a configuration file.
    """
    global custom_commands
    try:
        with open(config_file, 'r') as config_file:
            config_data = json.load(config_file)
            custom_commands = config_data.get('custom_commands', {})
    except FileNotFoundError:
        print("Custom command configuration file not found.")
    except json.JSONDecodeError as e:
        print(f"Error loading custom commands from the configuration file: {e}")

def main():
    load_session_data()  # Load session data if available

    parser = argparse.ArgumentParser(description="Coloby's Version Control and File Upload System")
    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # Initialize a new repository
    parser_init = subparsers.add_parser('init', help='Initialize a new repository')

    # Commit changes and add files to the upload queue
    parser_commit = subparsers.add_parser('commit', help='Create a commit and add files to the upload queue')
    parser_commit.add_argument('-m', '--message', required=True, help='Commit message')

    # Upload queued files to a room
    parser_upload = subparsers.add_parser('upload', help='Upload queued files to a room')
    parser_upload.add_argument('--room', required=True, help='Room name')

    # Authentication prompt
    parser_login = subparsers.add_parser('login', help='Log in with your credentials')

    args = parser.parse_args()

    if args.command == 'init':
        init_repo()
    elif args.command == 'commit':
        user_data = login_prompt()  # Prompt user for login and get user data
        if user_data:
            create_commit(args.message, user_data)  # Pass user data to create_commit
    elif args.command == 'upload':
        user_data = login_prompt()  # Prompt user for login and get user data
        if user_data:
            upload_queued_files(args.room, user_data)  # Pass user data to upload_queued_files

    if args.command == 'login':
        login_prompt()  # Prompt user for login

    # Start the Watchdog observer
    event_handler = MyHandler()
    observer = Observer()
    observer.schedule(event_handler, path=REPO_DIR, recursive=False)
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

if __name__ == '__main__':
    main()
