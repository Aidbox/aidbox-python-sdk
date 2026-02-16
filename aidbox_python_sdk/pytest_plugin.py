import asyncio
import importlib
import os
import threading
import warnings
from collections.abc import Generator
from types import SimpleNamespace

import pytest
from aiohttp import BasicAuth, ClientSession, web
from yarl import URL

from aidbox_python_sdk.aidboxpy import AsyncAidboxClient

from . import app_keys as ak

_TEST_SERVER_URL = "http://127.0.0.1:8081"


def pytest_addoption(parser):
    parser.addini(
        "aidbox_create_app",
        "Dotted path to the create_app callable (module:name or module.name), e.g. main:create_app",
        default="main:create_app",
    )


def _load_create_app(path: str):
    """Import and return the create_app callable from the given dotted path."""
    if ":" in path:
        module_path, attr = path.split(":", 1)
    else:
        module_path, attr = path.rsplit(".", 1)
    mod = importlib.import_module(module_path)
    return getattr(mod, attr)


@pytest.fixture(scope="session")
def create_app(request):
    """App factory; override in conftest or set pytest ini option aidbox_create_app."""
    path = request.config.getini("aidbox_create_app")
    return _load_create_app(path)


@pytest.fixture(scope="session", autouse=True)
def app(create_app) -> Generator[web.Application, None, None]:
    """Start the aiohttp application server in a background thread.

    Uses a dedicated event loop running continuously via loop.run_forever()
    in a daemon thread. This is necessary (rather than an async fixture) because
    the app needs the loop running at all times to handle external callbacks
    from Aidbox (subscriptions, SDK heartbeats, etc.), not just during await
    points in test code.

    The server is guaranteed to be listening before any test runs (no sleep-based
    waiting) since site.start() completes synchronously before yielding.
    """

    app = create_app()
    app[ak.sdk]._test_start_txid = -1
    loop = asyncio.new_event_loop()

    runner = web.AppRunner(app)
    loop.run_until_complete(runner.setup())
    site = web.TCPSite(runner, host="0.0.0.0", port=8081)
    loop.run_until_complete(site.start())

    thread = threading.Thread(target=loop.run_forever, daemon=True)
    thread.start()

    yield app

    loop.call_soon_threadsafe(loop.stop)
    thread.join(timeout=5)
    loop.run_until_complete(runner.cleanup())
    loop.close()


@pytest.fixture
async def client(app):
    server = SimpleNamespace(app=app)
    session = ClientSession(base_url=URL(_TEST_SERVER_URL))
    wrapper = SimpleNamespace(server=server)
    wrapper.get = session.get
    wrapper.post = session.post
    wrapper.put = session.put
    wrapper.patch = session.patch
    wrapper.delete = session.delete
    wrapper.request = session.request
    wrapper._session = session
    try:
        yield wrapper
    finally:
        await session.close()


@pytest.fixture
async def safe_db(aidbox_client: AsyncAidboxClient, sdk):
    results = await aidbox_client.execute(
        "/$psql",
        data={"query": "SELECT last_value from transaction_id_seq;"},
    )
    txid = results[0]["result"][0]["last_value"]
    sdk._test_start_txid = int(txid)

    yield txid

    sdk._test_start_txid = -1
    await aidbox_client.execute(
        "/$psql",
        data={"query": f"select drop_before_all({txid});"},
        params={"execute": "true"},
    )


@pytest.fixture
def sdk(app):
    return app[ak.sdk]


@pytest.fixture
def aidbox_client(app):
    return app[ak.client]


@pytest.fixture
async def aidbox_db(app):
    # We clone it to init client session in the test thread
    # because app is running in another thread with own loop
    db = app[ak.db].clone()
    await db.initialize()
    yield db
    await db.deinitialize()


# Deprecated
class AidboxSession(ClientSession):
    def __init__(self, *args, base_url=None, **kwargs):
        base_url_resolved = base_url or os.environ.get("AIDBOX_BASE_URL")
        assert base_url_resolved, "Either base_url arg or AIDBOX_BASE_URL env var must be set"
        self.base_url = URL(base_url_resolved)
        super().__init__(*args, **kwargs)

    def make_url(self, path):
        return self.base_url.with_path(path)

    async def _request(self, method, path, *args, **kwargs):
        url = self.make_url(path)
        return await super()._request(method, url, *args, **kwargs)


@pytest.fixture
async def aidbox(sdk, app):
    warnings.warn(
        "The 'aidbox' fixture is deprecated; use 'aidbox_client' for the Aidbox client instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    basic_auth = BasicAuth(
        login=app[ak.settings].APP_INIT_CLIENT_ID,
        password=app[ak.settings].APP_INIT_CLIENT_SECRET,
    )
    session = AidboxSession(auth=basic_auth, base_url=app[ak.settings].APP_INIT_URL)
    yield session
    await session.close()
