# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Copy the local 'app' directory contents into the container at /app
# This copies app.py and the templates folder
COPY ./app /app

# Install any needed packages (mysql-connector-python and Flask)
RUN pip install --no-cache-dir mysql-connector-python Flask

# Make port 5000 available to the world outside this container
EXPOSE 5000

# Command to run the application when the container starts
# It executes app.py
CMD ["python", "app.py"]
