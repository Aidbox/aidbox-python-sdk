import asyncio
import errno
import json
import logging
import os
import sys
from pathlib import Path

from aiohttp import BasicAuth, client_exceptions, web

from .aidboxpy import AsyncAidboxClient
from .db import DBProxy
from .handlers import routes
from .sdk import SDK
from .settings import Settings
from fhirpy.base.exceptions import OperationOutcome

logger = logging.getLogger("aidbox_sdk")
THIS_DIR = Path(__file__).parent
BASE_DIR = THIS_DIR.parent


def setup_routes(app):
    app.add_routes(routes)


async def register_app(sdk: SDK, client: AsyncAidboxClient):
    app_manifest = sdk.build_manifest()
    
    try:
        # We create app directly using execute to avoid conversion
        await client.execute(
            f"/App/{app_manifest['id']}", method="put", data=app_manifest)
        
        logger.info("Creating seeds and applying migrations")
        await sdk.create_seed_resources(client)
        await sdk.apply_migrations(client)
        logger.info("Aidbox app successfully registered")
    except OperationOutcome as error:
        logger.error(
            "Error during the App registration: %s", json.dumps(error, indent=2)
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


async def init_client(settings: Settings):
    AidboxClient = settings.AIDBOX_CLIENT_CLASS
    basic_auth = BasicAuth(
        login=settings.APP_INIT_CLIENT_ID,
        password=settings.APP_INIT_CLIENT_SECRET,
    )

    return AidboxClient(
        "{}".format(settings.APP_INIT_URL), authorization=basic_auth.encode()
    )


async def init(app):
    app["client"] = await init_client(app["settings"])
    app["db"] = DBProxy(app["settings"])
    await app["db"].initialize()
    await register_app(app["sdk"], app["client"])
    yield
    await app["db"].deinitialize()


def create_app(sdk: SDK):
    app = web.Application()
    app.cleanup_ctx.append(init)
    app.update(
        settings=sdk.settings,
        sdk=sdk,
    )
    setup_routes(app)
    return app
