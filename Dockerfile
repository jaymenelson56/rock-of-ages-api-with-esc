# Use Python as the base image
FROM python:latest

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
# Set this to find the virtual environment
ENV PIPENV_VENV_IN_PROJECT=1

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
  gcc \
  && rm -rf /var/lib/apt/lists/*

# Install pipenv
RUN pip install --upgrade pip && \
  pip install pipenv

# Copy Pipfile and Pipfile.lock
COPY Pipfile* /app/

# Install dependencies in a virtual environment
RUN pipenv install

# Copy project files
COPY . /app/

# Make the seed_database.sh script executable
RUN chmod +x /app/seed_database.sh

# Expose port
EXPOSE 8000

# Command to run scripts using the pipenv environment
CMD ["pipenv", "run", "bash", "-c", "sed -i 's/\r$//' seed_database.sh && ./seed_database.sh && python manage.py runserver 0.0.0.0:8000"]