FROM 719056139938.dkr.ecr.us-east-2.amazonaws.com/hirin:python3.10.12-slim

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
RUN pip install --no-cache-dir -r requirements.txt

# Create a non-root user and set appropriate permissions
RUN useradd -M -d /app appuser && chown -R appuser:appuser /app

# Switch to the non-root user
USER appuser

ENV PATH=/usr/local/cuda-11.2/bin${PATH:+:${PATH}}
ENV LD_LIBRARY_PATH=/usr/local/cuda-11.2/lib64${LD_LIBRARY_PATH:+:${LD_LIBRARY_PATH}}

# Expose the application port
#EXPOSE 5009

# Run the application

CMD ["python3", "main.py"]

