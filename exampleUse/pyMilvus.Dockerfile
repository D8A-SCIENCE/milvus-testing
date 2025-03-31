FROM python:3.9-slim

# Install dependencies required for pymilvus
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Install pymilvus
RUN pip install --no-cache-dir pymilvus==2.2.11

# Set the working directory
WORKDIR /app

# Command to keep the container running
CMD ["bash"]
