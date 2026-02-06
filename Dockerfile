FROM python:3.12-slim

LABEL maintainer="pentafive"
LABEL description="ClubLog to Home Assistant MQTT Bridge"
LABEL version="0.2.1"

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY clublog-ha-bridge.py .
COPY config.py .

CMD ["python3", "-u", "clublog-ha-bridge.py"]
