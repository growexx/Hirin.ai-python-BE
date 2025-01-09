FROM python:3.10.12-slim

# Install necessary dependencies for OpenCV and clean up apt cache
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Set the working directory
WORKDIR /app

# Copy the application files
COPY . .

# Install Python dependencies without cache
RUN pip install --no-cache-dir -r app/requirements.txt

# Create a non-root user and set appropriate permissions
RUN useradd -M appuser && chown -R appuser:appuser /app

# Switch to the non-root user
USER appuser

# Expose the application port
EXPOSE 5009

# Run the application
CMD ["python3", "app/main.py"]
