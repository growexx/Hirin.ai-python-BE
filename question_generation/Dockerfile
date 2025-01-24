FROM 719056139938.dkr.ecr.us-east-2.amazonaws.com/hirin:python3.13-alpine

# Install build dependencies
RUN apk add --no-cache \
    build-base \
    linux-headers \
    meson \
    ninja \
    gfortran \
    openblas-dev

WORKDIR /app

COPY . .

RUN pip install --no-cache-dir -r requirements.txt

RUN adduser -D appuser && chown -R appuser:appuser /app

USER appuser

EXPOSE 5001

CMD ["hypercorn", "run:app", "--bind", "0.0.0.0:5001", "--reload"]
