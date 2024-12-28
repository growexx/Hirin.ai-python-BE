FROM python:3.12-alpine

WORKDIR /app

COPY . .

RUN pip install -r requirements.txt

RUN adduser -D grs-user && chown -R grs-user:grs-user /app

USER grs-user

EXPOSE 5000

CMD ["python3", "run.py", "--host=0.0.0.0", "--port=5000"]
