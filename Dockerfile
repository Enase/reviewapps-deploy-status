FROM python:3.7-alpine

RUN pip install --upgrade pip
RUN pip install requests==2.28.1

WORKDIR /app
COPY . .

CMD ["python3", "/app/review_app_status.py"]
