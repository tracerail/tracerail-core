# Use a slim, official Python base image.
FROM python:3.11-slim

# Set environment variables for best practices.
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    POETRY_VERSION=1.8.2 \
    # Tell Poetry to create the virtual environment inside the project directory.
    POETRY_VIRTUALENVS_IN_PROJECT=true

# Install Poetry system-wide.
RUN pip install "poetry==$POETRY_VERSION"

# Set the working directory for the application.
WORKDIR /app

# Copy the project files and install dependencies.
# This is done first to leverage Docker's layer caching, making subsequent
# builds much faster if dependencies haven't changed.
COPY pyproject.toml poetry.lock ./
RUN poetry install --only main

# Copy the application source code into the container.
COPY tracerail/ ./tracerail/

# Set the command to run when the container starts.
# We use `python -m tracerail.worker` to run the worker as a module, which
# correctly handles Python's import path.
CMD ["poetry", "run", "python", "-m", "tracerail.worker"]
