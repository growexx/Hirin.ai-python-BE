FROM python:3.10-alpine

WORKDIR /app

COPY . .

RUN pip install --no-cache-dir -r requirements.txt

RUN adduser -D appuser && chown -R appuser:appuser /app

USER appuser

EXPOSE 5001

CMD ["python3", "run.py"]
