# Use an official Python runtime as a parent image
FROM python:3.12-slim

# Set environment variables to avoid prompts during installation
ENV DEBIAN_FRONTEND=noninteractive

# Install system dependencies and TA-Lib
RUN apt-get update && \
    apt-get install -y \
    build-essential \
    wget \
    libtool \
    pkg-config \
    libssl-dev \
    libbz2-dev \
    libreadline-dev \
    libsqlite3-dev \
    curl \
    zlib1g-dev \
    libncurses5-dev \
    libgdbm-dev \
    libnss3-dev \
    libffi-dev \
    liblzma-dev \
    tk-dev \
    libxml2-dev \
    libxmlsec1-dev \
    libxslt1-dev \
    git \
    && rm -rf /var/lib/apt/lists/*

# Download and install TA-Lib
RUN wget https://github.com/AbyvargheseMandapathel/Gold-Trading-Dashboard/blob/v1/ta-lib_0.6.4_amd64.deb -O /tmp/ta-lib_0.6.4_amd64.deb && \
    sudo dpkg -i /tmp/ta-lib_0.6.4_amd64.deb && \
    sudo apt-get install -f -y && \
    rm /tmp/ta-lib_0.6.4_amd64.deb

# Set the working directory to /app
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose the port the app runs on
EXPOSE 8501

# Command to run the application
CMD ["streamlit", "run", "app.py"]
