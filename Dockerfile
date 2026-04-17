#FROM ubuntu:latest
#LABEL authors="yersultan"
#
#ENTRYPOINT ["top", "-b"]

# Dockerfile
FROM python:3.11-slim

WORKDIR /app

#Installing Dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

#copy project
COPY . .

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]