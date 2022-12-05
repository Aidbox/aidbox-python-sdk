#!/bin/bash

docker-compose -f docker-compose.yaml up --exit-code-from app app
