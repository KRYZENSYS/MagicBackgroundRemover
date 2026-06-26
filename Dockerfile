FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1 PIP_NO_CACHE_DIR=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libpq-dev libgl1 libglib2.0-0 libsm6 libxrender1 libxext6 \
    libgomp1 curl ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install --extra-index-url https://download.pytorch.org/whl/cpu torch && \
    pip install -r requirements.txt

COPY . .

RUN chmod +x railway_start.sh render_start.sh && mkdir -p /data/models /app/logs

EXPOSE 8080

CMD ["./railway_start.sh"]