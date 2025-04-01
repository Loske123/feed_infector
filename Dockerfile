FROM python:3.6-slim

# Set the working directory inside the container
WORKDIR /app

# Install system dependencies including ffmpeg and imagemagick
RUN apt-get update && apt-get install -y 

# Copy your requirements.txt file
COPY requirements.txt .

# Install dependencies
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Copy your project files into the container
COPY . .

# Default command (optional)
CMD ["python"]