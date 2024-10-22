# aidbox-python-sdk-example

# Development

## Local environment setup

1. Install pyenv and poetry globally
2. Install python3.12 python globally using pyenv
3. Inside the app directory, run `poetry env use /path/to/python312`
4. Run `poetry install`
5. Run `poetry shell` to activate virtual environment
6. Run `autohooks activate` to activate git hooks

## Local deployment
0. Run Aidbox anywhere but make `host.docker.internal` available from the Aidbox to access the host machine
1. Run `cp .env.example .env`
2. `docker-compose up`

## Testing

1. Run `cp .env.tests.local.example .env.tests.local`
2. Put your dev aidbox license key into `AIDBOX_LICENSE_TEST` in `.env.tests.local`
3. Run `docker compose -f compose.test-env.yaml build` at the first time and every time once dependencies are updated/added
4. Run `./run_test.sh`
5. You can kill the containers when complete to work with tests by run:
   `docker compose -f compose.test-env.yaml down`

## IDE setup

Strongly recommended to use ruff and mypy plugins for IDE
