FROM python:3.12-alpine

WORKDIR /app

COPY . .

RUN pip install --no-cache-dir -r requirements.txt

# Create a non-root user and set appropriate permissions
RUN adduser -D appuser && chown -R appuser:appuser /app

USER appuser

EXPOSE 5000

CMD ["python3", "run.py"]
