import asyncio
import errno
import logging
import os
import sys
from pathlib import Path

from aidboxpy import AsyncAidboxClient
from aiohttp import BasicAuth, ClientSession, client_exceptions, web

from .handlers import routes

logger = logging.getLogger("aidbox_sdk")
THIS_DIR = Path(__file__).parent
BASE_DIR = THIS_DIR.parent


def setup_routes(app):
    app.add_routes(routes)


async def init_aidbox(app):
    try:
        async with app["init_http_client"].put(
            "{}/App".format(app["settings"].APP_INIT_URL),
            json={
                "resourceType": "App",
                "apiVersion": 1,
                "type": "app",
                "id": app["settings"].APP_ID,
                "endpoint": {
                    "url": app["settings"].APP_URL,
                    "type": "http-rpc",
                    "secret": app["settings"].APP_SECRET,
                },
                **app["sdk"].build_manifest(),
            },
        ) as resp:
            if 200 <= resp.status < 300:
                logger.info("Initializing Aidbox app...")
                await app["sdk"].initialize(app["client"])
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
            "Aidbox address is unreachable {}".format(app["settings"].APP_INIT_URL)
        )
        sys.exit(errno.EINTR)


async def wait_aidbox(app):
    address = app["settings"].APP_URL
    logger.debug("Check availability of {}".format(address))
    while 1:
        try:
            async with app["init_http_client"].get(address, timeout=5):
                pass
            break
        except (
            asyncio.TimeoutError,
            client_exceptions.InvalidURL,
            client_exceptions.ClientConnectionError,
        ):
            await asyncio.sleep(2)


async def wait_and_init_aidbox(app):
    await wait_aidbox(app)
    await init_aidbox(app)


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


async def on_startup(app):
    await init_http_client(app)
    await init_aidbox_client(app)

    asyncio.get_event_loop().create_task(wait_and_init_aidbox(app))


async def on_cleanup(app):
    await app["init_http_client"].close()
    await app["sdk"].deinitialize()


async def on_shutdown(app):
    if not app["init_http_client"].closed:
        await app["init_http_client"].close()


async def create_app(settings, sdk, debug=False):
    sdk.is_ready = asyncio.Future()
    app = web.Application()
    app.on_startup.append(on_startup)
    app.on_cleanup.append(on_cleanup)
    app.on_shutdown.append(on_shutdown)
    app.update(
        name="aidbox-python-sdk",
        settings=settings,
        sdk=sdk,
        init_aidbox_app=init_aidbox,
        livereload=True,
    )
    setup_routes(app)
    return app
