FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . /app


EXPOSE ${ASR_PORT}


CMD ["sh", "-c", "uvicorn app.main:app --host ${HOST} --port ${ASR_PORT}"]
