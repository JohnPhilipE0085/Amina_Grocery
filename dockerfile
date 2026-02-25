FROM python:3.11-slim

# 2. Set environment variables
# Prevents Python from writing .pyc files to the container
ENV PYTHONDONTWRITEBYTECODE 1
# ensures console output is exported in real-time
ENV PYTHONUNBUFFERED 1

WORKDIR /app

# 4. Install system dependencies (needed for some Python packages)
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# 5. Install Python dependencies
# Copy only the requirements file first to leverage Docker caching
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# 6. Copy the rest of your Django project code into the container
COPY . /app/

# 7. Expose the port Django runs on
EXPOSE 8000

# 8. The command to run the application
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]