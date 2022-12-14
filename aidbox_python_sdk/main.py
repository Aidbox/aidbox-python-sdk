import asyncio
import errno
import logging
import os
import sys
from pathlib import Path

from aiohttp import BasicAuth, ClientSession, client_exceptions, web

from .aidboxpy import AsyncAidboxClient
from .db import DBProxy
from .handlers import routes
from .sdk import SDK

logger = logging.getLogger("aidbox_sdk")
THIS_DIR = Path(__file__).parent
BASE_DIR = THIS_DIR.parent


def setup_routes(app):
    app.add_routes(routes)


async def register_app(
    sdk: SDK, *, http_client: ClientSession, aidbox_client: AsyncAidboxClient
):
    try:
        async with http_client.put(
            "{}/App".format(sdk.settings.APP_INIT_URL),
            json={
                "resourceType": "App",
                "apiVersion": 1,
                "type": "app",
                "id": sdk.settings.APP_ID,
                "endpoint": {
                    "url": sdk.settings.APP_URL,
                    "type": "http-rpc",
                    "secret": sdk.settings.APP_SECRET,
                },
                **sdk.build_manifest(),
            },
        ) as resp:
            if 200 <= resp.status < 300:
                logger.info("Initializing Aidbox app...")
                await sdk.initialize(aidbox_client)
            else:
                logger.error(
                    "Aidbox app initialized failed. "
                    "Response from Aidbox: {0} {1}".format(
                        resp.status, await resp.text()
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


async def init_http_client(app):
    basic_auth = BasicAuth(
        login=app["settings"].APP_INIT_CLIENT_ID,
        password=app["settings"].APP_INIT_CLIENT_SECRET,
    )
    app["init_http_client"] = ClientSession(auth=basic_auth)


async def init_aidbox_client(app):
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
    await init_http_client(app)
    await init_aidbox_client(app)
    await init_db(app)

    await register_app(
        app["sdk"], http_client=app["init_http_client"], aidbox_client=app["client"]
    )


async def on_cleanup(app):
    await app["init_http_client"].close()
    await app["db"].deinitialize()
    await app["sdk"].deinitialize()


async def on_shutdown(app):
    if not app["init_http_client"].closed:
        await app["init_http_client"].close()


def create_app(sdk: SDK):
    sdk.is_ready = asyncio.Future()
    app = web.Application()
    app.on_startup.append(on_startup)
    app.on_cleanup.append(on_cleanup)
    app.on_shutdown.append(on_shutdown)
    app.update(
        name="aidbox-python-sdk",
        settings=sdk.settings,
        sdk=sdk,
    )
    setup_routes(app)
    return app
