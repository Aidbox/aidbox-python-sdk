import errno
import json
import logging
import sys
from pathlib import Path
from typing import cast

from aiohttp import BasicAuth, client_exceptions, web
from fhirpy.base.exceptions import OperationOutcome

from . import app_keys as ak
from .aidboxpy import AsyncAidboxClient
from .db import DBProxy
from .handlers import routes
from .sdk import SDK
from .settings import Settings

logger = logging.getLogger("aidbox_sdk")
THIS_DIR = Path(__file__).parent
BASE_DIR = THIS_DIR.parent


def setup_routes(app):
    app.add_routes(routes)


async def register_app(sdk: SDK, client: AsyncAidboxClient):
    app_manifest = sdk.build_manifest()

    try:
        # We create app directly using execute to avoid conversion
        await client.execute(f"/App/{app_manifest['id']}", method="put", data=app_manifest)

        logger.info("Creating seeds and applying migrations")
        await sdk.create_seed_resources(client)
        await sdk.apply_migrations(client)
        logger.info("Aidbox app successfully registered")
    except OperationOutcome as error:
        logger.error("Error during the App registration: %s", json.dumps(error, indent=2))
        sys.exit(errno.EINTR)
    except (
        client_exceptions.ServerDisconnectedError,
        client_exceptions.ClientConnectionError,
    ):
        logger.error("Aidbox address is unreachable %s", sdk.settings.APP_INIT_URL)
        sys.exit(errno.EINTR)


async def init_client(settings: Settings):
    aidbox_client_cls = settings.AIDBOX_CLIENT_CLASS
    basic_auth = BasicAuth(
        login=cast(str, settings.APP_INIT_CLIENT_ID),
        password=cast(str, settings.APP_INIT_CLIENT_SECRET),
    )

    return aidbox_client_cls(f"{settings.APP_INIT_URL}", authorization=basic_auth.encode())


async def init(app: web.Application):
    app[ak.client] = await init_client(app[ak.settings])
    app["client"] = app[ak.client]  # For backwards compatibility
    app[ak.db] = DBProxy(app[ak.settings])
    app["db"] = app[ak.db]  # For backwards compatibility
    await register_app(app[ak.sdk], app[ak.client])
    await app[ak.db].initialize()
    yield
    await app[ak.db].deinitialize()


def create_app(sdk: SDK):
    app = web.Application()
    app.cleanup_ctx.append(init)
    app[ak.sdk] = sdk
    app["sdk"] = app[ak.sdk]  # For backwards compatibility
    app[ak.settings] = sdk.settings
    app["settings"] = app[ak.settings]  # For backwards compatibility

    setup_routes(app)
    return app
