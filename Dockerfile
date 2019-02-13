FROM python:3
RUN mkdir /app
WORKDIR /app

COPY . .
RUN pip install --no-cache-dir -r ./requirements/base.txt -r ./requirements/dev.txt

EXPOSE 8081
