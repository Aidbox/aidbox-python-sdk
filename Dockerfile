ARG PYTHON_VERSION
FROM python:$PYTHON_VERSION
RUN pip install pipenv

RUN mkdir /app
WORKDIR /app

COPY Pipfile Pipfile.lock ./
RUN pipenv install --dev

RUN pipenv check
COPY . .

EXPOSE 8081
