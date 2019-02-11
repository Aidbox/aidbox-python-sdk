"""
This file allows your to serve your application using gunicorn. gunicorn is not installed by default
by the requirements file adev creates, you'll need to install it yourself and add it to requirements.txt.

To run the aidbox_python_sdk using gunicorn, in the terminal run

    pip install gunicorn
    gunicorn aidbox_python_sdk.gunicorn:aidbox_python_sdk --worker-class aiohttp.worker.GunicornWebWorker

You could use a variant of the above with heroku (in the `Procfile`) or with Docker in the ENTRYPOINT statement.
"""
import asyncio
import uvloop

from .main import create_app

uvloop.install()
loop = asyncio.get_event_loop()

app = loop.run_until_complete(create_app())
