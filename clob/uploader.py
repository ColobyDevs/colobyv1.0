import requests
import getpass
import json
import os
import argparse


BASE_URL = 'http://127.0.0.1:8000'  

# Path to store session data
SESSION_DATA_FILE = 'session_data.json'

def save_session_data(session_data):
    with open(SESSION_DATA_FILE, 'w') as file:
        json.dump(session_data, file)

def load_session_data():
    try:
        with open(SESSION_DATA_FILE, 'r') as file:
            return json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def authenticate_user():
    session_data = load_session_data()
    if 'email' in session_data and 'token' in session_data:
        print("You are already authenticated as", session_data['email'])
        return session_data

    email = input("Enter your email: ")
    password = getpass.getpass("Enter your password: ")

    login_url = f"{BASE_URL}/api/auth/log-in/"
    credentials = {'email': email, 'password': password}

    try:
        response = requests.post(login_url, data=credentials)
        response.raise_for_status()

        if response.status_code == 200:
            print("Authentication successful!")
            session_data = {'email': email, 'token': response.json().get('token')}
            save_session_data(session_data)
            return session_data
        else:
            print("Authentication failed. Please check your email and password.")

    except requests.exceptions.RequestException as e:
        print(f"Authentication failed: {e}")

    return {}

'''
Upload Files

'''

def upload_file(session_data):
    if 'token' not in session_data:
        print("Please authenticate first.")
        return

    room_link = input("Enter the room link: ")
    file_path = input("Enter the file path to upload: ")

    # Check if the user is authenticated and get their user information
    if 'email' not in session_data:
        print("Please authenticate first.")
        return

    email = session_data['email']

    upload_url = f"{BASE_URL}/api/v1/chat/upload/{room_link}/"
    headers = {'Authorization': f'Token {session_data["token"]}'}

    try:
        with open(file_path, 'rb') as file:
            files = {'file': file}
            description = input("Enter a file description (optional): ")
            data = {'description': description, 'user_email': email}  # Send the user's email
            response = requests.post(upload_url, headers=headers, files=files, data=data)
            response.raise_for_status()

            if response.status_code == 200:
                print("File uploaded successfully.")
            else:
                print("File upload failed. You may not have permission to upload this file to the room.")
                

    except FileNotFoundError:
        print(f"File not found: {file_path}")
    except requests.exceptions.RequestException as e:
        print(f"File upload failed: {e}")




'''
Retrieve Files

'''


def retrieve_files(session_data):
    if 'token' not in session_data:
        print("Please authenticate first.")
        return

    room_link = input("Enter the room link: ")

    # Create a directory to save the downloaded files
    download_dir = 'downloaded_files'
    os.makedirs(download_dir, exist_ok=True)

    download_url = f"{BASE_URL}/api/v1/chat/files/{room_link}/"
    headers = {'Authorization': f'Token {session_data["token"]}'}

    try:
        response = requests.get(download_url, headers=headers)

        if response.status_code == 200:
            files = response.json()
            for file_info in files:
                file_id = file_info['id']
                file_name = file_info['file']
                file_path = os.path.join(download_dir, file_name)

                # Download the file
                response = requests.get(f"{download_url}/{file_id}/", headers=headers)
                if response.status_code == 200:
                    with open(file_path, 'wb') as f:
                        f.write(response.content)
                    print(f"Downloaded file: {file_name} to {file_path}")
                else:
                    print(f"Failed to download file: {file_name}")

            print("All files downloaded successfully.")
        else:
            print("Failed to retrieve files from the room. You may not have permission to access this room or the room may not exist.")

    except requests.exceptions.RequestException as e:
        print(f"File retrieval failed: {e}")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="CLOB CLI")
    parser.add_argument("action", choices=["upload", "retrieve"], help="Choose 'upload' or 'retrieve'")

    args = parser.parse_args()

    session_data = authenticate_user()

    if args.action == "upload":
        upload_file(session_data)
    elif args.action == "retrieve":
        retrieve_files(session_data)
