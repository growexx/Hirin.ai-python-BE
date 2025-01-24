FROM python:3.13-alpine

WORKDIR /app

COPY . .

RUN pip install --no-cache-dir -r requirements.txt

RUN adduser -D appuser && chown -R appuser:appuser /app

USER appuser

EXPOSE 5001

CMD ["hypercorn", "run:app", "--bind", "0.0.0.0:5001", "--reload"]
