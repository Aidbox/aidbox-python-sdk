import logging
from collections.abc import AsyncGenerator

from aidbox_python_sdk.main import init_client, register_app, setup_routes
from aidbox_python_sdk.settings import Settings
from aiohttp import BasicAuth, ClientSession, web
from fhirpy import AsyncFHIRClient

from app import app_keys as ak
from app import config, operations  # noqa: F401
from app.sdk import sdk

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)


async def init_fhir_client(settings: Settings, prefix: str = "") -> AsyncFHIRClient:
    basic_auth = BasicAuth(
        login=settings.APP_INIT_CLIENT_ID,
        password=settings.APP_INIT_CLIENT_SECRET,
    )

    return AsyncFHIRClient(
        f"{settings.APP_INIT_URL}{prefix}",
        authorization=basic_auth.encode(),
        dump_resource=lambda x: x.model_dump(),
    )


async def fhir_client_ctx(app: web.Application) -> AsyncGenerator[None, None]:
    app[ak.fhir_client] = await init_fhir_client(app[ak.settings], "/fhir")
    yield


async def client_ctx(app: web.Application) -> AsyncGenerator[None, None]:
    app[ak.client] = await init_client(app[ak.settings])
    yield


async def app_ctx(app: web.Application) -> AsyncGenerator[None, None]:
    await register_app(app[ak.sdk], app[ak.client])
    yield


async def client_session_ctx(app: web.Application) -> AsyncGenerator[None, None]:
    session = ClientSession()
    app[ak.session] = session
    yield
    await session.close()


def create_app() -> web.Application:
    app = web.Application()
    app[ak.sdk] = sdk
    app[ak.settings] = sdk.settings
    app.cleanup_ctx.append(client_session_ctx)
    app.cleanup_ctx.append(client_ctx)
    app.cleanup_ctx.append(fhir_client_ctx)
    app.cleanup_ctx.append(app_ctx)

    setup_routes(app)

    return app


async def create_gunicorn_app() -> web.Application:
    return create_app()
