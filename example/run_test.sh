#!/bin/sh

if [ -f ".env.tests.local" ]; then
    export `cat .env.tests.local`
fi

if [ -z "${AIDBOX_LICENSE_TEST}" ]; then
    echo "AIDBOX_LICENSE_TEST is required to run tests"
    exit 1
fi


docker compose -f compose.test-env.yaml pull --quiet
docker compose -f compose.test-env.yaml up --exit-code-from app app

exit $?
