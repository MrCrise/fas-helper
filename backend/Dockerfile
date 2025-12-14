FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    gcc python3-dev libpq-dev curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .

RUN sed -i '/pywin32/d' requirements.txt && \
    pip install --no-cache-dir -r requirements.txt

EXPOSE 8000

CMD ["python", "api.py"]
