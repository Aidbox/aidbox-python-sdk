#!/usr/bin/env bash
# App settings go here, they're validated in app.settings

# the AIO_ env variables are used by `adev runserver` when serving your app for development
export AIO_APP_PATH="aidbox_python_sdk/"
export $(grep -v '^#' .env | xargs)

# also activate the python virtualenv for convenience, you can remove this if you're python another way
. env/bin/activate
