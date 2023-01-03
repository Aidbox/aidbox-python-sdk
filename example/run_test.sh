#!/bin/sh

if [ -f ".env" ]; then
    export `cat .env`
fi

if [ -z "${TESTS_AIDBOX_LICENSE}" ]; then
    echo "TESTS_AIDBOX_LICENSE is required to run tests"
    exit 1
fi

export TEST_COMMAND="pipenv run pytest --cov app ${@:-tests/}"
docker compose -f docker-compose.tests.yaml up --exit-code-from backend backend
exit $?
