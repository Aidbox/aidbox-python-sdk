#!/bin/sh

if [ -f "envs/aidbox" ]; then
    export `cat envs/aidbox`
fi

if [ -z "${AIDBOX_LICENSE}" ]; then
    echo "AIDBOX_LICENSE is required to run tests"
    exit 1
fi


docker compose -f docker-compose.yaml pull --quiet
docker compose -f docker-compose.yaml up --exit-code-from app app

exit $?
