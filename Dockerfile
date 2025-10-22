FROM python:3.11-slim-buster

WORKDIR /app

COPY ./server/requirements.txt /app/server/requirements.txt
RUN pip install --no-cache-dir --upgrade -r /app/server/requirements.txt

COPY ./server /app/server
EXPOSE 8082

CMD ["uvicorn", "server.main:app", "--host", "0.0.0.0", "--port", "8082"]