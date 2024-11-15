FROM python:3.12-slim

RUN addgroup --gid 1000 dockeruser
RUN adduser --disabled-login --uid 1000 --gid 1000 dockeruser
RUN mkdir -p /app/
RUN chown -R dockeruser:dockeruser /app/

RUN pip install poetry

USER dockeruser

WORKDIR /app

COPY pyproject.toml .
COPY poetry.lock .
RUN poetry install

COPY . .

RUN poetry run mypy

CMD ["poetry", "run", "gunicorn", "main:create_gunicorn_app", "--worker-class", "aiohttp.worker.GunicornWebWorker", "-b", "0.0.0.0:8081"]
