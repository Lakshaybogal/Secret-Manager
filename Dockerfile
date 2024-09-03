# Use the official Python image from the Alpine distribution
FROM python:3.12.5-alpine3.20

# Set the working directory in the container
WORKDIR /app

# Install dependencies
RUN apk add --no-cache wget postgresql-client bash

# Copy the requirements.txt file into the container
COPY requirements.txt /app/

# Install any dependencies specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Download wait-for-it script
RUN wget -O /usr/local/bin/wait-for-it.sh https://raw.githubusercontent.com/vishnubob/wait-for-it/master/wait-for-it.sh \
    && chmod +x /usr/local/bin/wait-for-it.sh

# Copy the entire project into the container
COPY . /app

# Expose port 8000 to allow access to the Django app
EXPOSE 8000

# Set the entry point to run the application
CMD ["sh", "-c", "wait-for-it.sh db:5432 --timeout=30 --strict && python3 manage.py makemigrations && python3 manage.py migrate && python3 manage.py runserver 0.0.0.0:8000"]
