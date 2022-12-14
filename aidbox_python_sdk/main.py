import asyncio
import errno
import json
import logging
import os
import sys
from pathlib import Path

from aiohttp import BasicAuth, ClientSession, client_exceptions, web

from .aidboxpy import AsyncAidboxClient
from .db import DBProxy
from .handlers import routes
from .sdk import SDK
from fhirpy.base.exceptions import OperationOutcome

logger = logging.getLogger("aidbox_sdk")
THIS_DIR = Path(__file__).parent
BASE_DIR = THIS_DIR.parent


def setup_routes(app):
    app.add_routes(routes)


async def register_app(sdk: SDK, client: AsyncAidboxClient):
    app_resource = client.resource(
        "App",
        **{
            "apiVersion": 1,
            "type": "app",
            "id": sdk.settings.APP_ID,
            "endpoint": {
                "url": sdk.settings.APP_URL,
                "type": "http-rpc",
                "secret": sdk.settings.APP_SECRET,
            },
            **sdk.build_manifest(),
        }
    )
    try:
        try:
            await app_resource.save()
            logger.info("Creating seeds and applying migrations")
            await sdk.initialize(client)
        except OperationOutcome as error:
            logger.error(
                "Error during the App registration: {}".format(
                    json.dumps(error, indent=2)
                )
            )
            sys.exit(errno.EINTR)
    except (
        client_exceptions.ServerDisconnectedError,
        client_exceptions.ClientConnectionError,
    ):
        logger.error(
            "Aidbox address is unreachable {}".format(sdk.settings.APP_INIT_URL)
        )
        sys.exit(errno.EINTR)


async def init_client(app):
    basic_auth = BasicAuth(
        login=app["settings"].APP_INIT_CLIENT_ID,
        password=app["settings"].APP_INIT_CLIENT_SECRET,
    )

    app["client"] = AsyncAidboxClient(
        "{}".format(app["settings"].APP_INIT_URL), authorization=basic_auth.encode()
    )


async def init_db(app):
    # TODO: make DBProxy independent from the App
    app["db"] = DBProxy(app["settings"])
    await app["db"].initialize()


async def on_startup(app):
    await init_client(app)
    await init_db(app)

    await register_app(app["sdk"], app["client"])


async def on_cleanup(app):
    await app["db"].deinitialize()
    await app["sdk"].deinitialize()


def create_app(sdk: SDK):
    sdk.is_ready = asyncio.Future()
    app = web.Application()
    app.on_startup.append(on_startup)
    app.on_cleanup.append(on_cleanup)
    app.update(
        name="aidbox-python-sdk",
        settings=sdk.settings,
        sdk=sdk,
    )
    setup_routes(app)
    return app
