FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE ${TTS_PORT}


CMD ["sh", "-c", "uvicorn app.main:app --host ${HOST} --port ${TTS_PORT}"]