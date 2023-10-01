# Use the official Python image from Docker Hub
FROM python:3.10

ENV PYTHONBUFFERED=1

# Set the working directory inside the container
WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt .

# Install project dependencies
RUN pip install -r requirements.txt

# Copy the entire project into the container
COPY . .

# Expose the port your application will run on (change as needed)
EXPOSE 8000


# Define the command to run your application
CMD ["python3", "manage.py", "runserver"]


