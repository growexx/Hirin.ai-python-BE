FROM 719056139938.dkr.ecr.us-east-2.amazonaws.com/hirin:python3.11.5-alpine

WORKDIR /app

# Install build tools and dependencies, including portaudio
RUN apk add --no-cache \
    build-base \
    gcc \
    musl-dev \
    portaudio-dev \
    sdl2-dev \
    sdl2_image-dev \
    sdl2_mixer-dev \
    sdl2_ttf-dev \
    libffi-dev \
    freetype-dev \
    libpng-dev \
    jpeg-dev \
    zlib-dev \
    bash

# Copy application files
COPY . .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Create a non-root user and set permissions
RUN adduser -D appuser && chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Expose the application port
EXPOSE 5001

# Command to run the application
CMD ["python3", "Main_AI_Call.py"]
