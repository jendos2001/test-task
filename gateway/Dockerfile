FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt ./

RUN pip install -r requirements.txt

COPY . .

EXPOSE ${GATEWAY_PORT}


CMD ["sh", "-c", "uvicorn app.main:app --host ${HOST} --port ${GATEWAY_PORT}"]