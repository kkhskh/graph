FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    iproute2 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Copy the scripts directory
COPY scripts /app/scripts

# Install the package in development mode
RUN pip install -e .

# Expose the port the app runs on
EXPOSE 5000

# Command to run the application
CMD ["python", "scripts/run_monitoring.py"] 