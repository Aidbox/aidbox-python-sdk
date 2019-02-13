FROM python:3
RUN mkdir /app
WORKDIR /app

COPY ./requirements ./requirements
RUN pip install --no-cache-dir -r ./requirements/base.txt -r ./requirements/dev.txt
COPY . .

EXPOSE 8081
