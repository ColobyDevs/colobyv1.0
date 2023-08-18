import sys
from cowork.management.commands.upload_files import Command as UploadFilesCommand
from django.core.exceptions import ValidationError


def main():
    if len(sys.argv) < 4:
        print(
            "Usage: colup <username> <room_slug> <file_or_folder_path> ")
        sys.exit(1)

    username = sys.argv[1]
    room_slug = sys.argv[2]
    paths = sys.argv[3:]

    try:
        command = UploadFilesCommand()
        command.handle(username, room_slug, *paths)
    except ValidationError as ve:
        print(f"Validation Error: {ve.message}")
        sys.exit(1)
    except Exception as e:
        print(f"An error occurred: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
