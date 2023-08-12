import asyncio
import pytest_asyncio
import pytest
import os
from yarl import URL
from aiohttp import ClientSession, BasicAuth, hdrs
from aiohttp.test_utils import TestServer, TestClient, BaseTestServer
from aiohttp.web import Application
from aiohttp.client import _RequestContextManager

from main import create_app as _create_app


async def start_app(aiohttp_client):
    app = await aiohttp_client(
        _create_app(), server_kwargs={"host": "0.0.0.0", "port": 8081}
    )
    sdk = app.server.app["sdk"]
    sdk._test_start_txid = -1

    return app


@pytest.fixture
def client(event_loop, aiohttp_client):
    """Instance of app's server and client"""
    return event_loop.run_until_complete(start_app(aiohttp_client))


class AidboxSession(ClientSession):
    def __init__(self, *args, base_url=None, **kwargs):
        self.base_url = URL(base_url or os.environ.get("AIDBOX_BASE_URL"))
        super().__init__(*args, **kwargs)

    def make_url(self, path):
        return self.base_url.with_path(path)

    async def _request(self, method, path, *args, **kwargs):
        url = self.make_url(path)
        return await super()._request(method, url, *args, **kwargs)


@pytest_asyncio.fixture
async def aidbox(client):
    """HTTP client for making requests to Aidbox"""
    app = client.server.app
    basic_auth = BasicAuth(
        login=app["settings"].APP_INIT_CLIENT_ID,
        password=app["settings"].APP_INIT_CLIENT_SECRET,
    )
    session = AidboxSession(auth=basic_auth)
    yield session
    await session.close()


@pytest_asyncio.fixture
async def safe_db(aidbox, client):
    sdk = client.server.app["sdk"]

    resp = await aidbox.post(
        "/$psql",
        json={"query": "SELECT last_value from transaction_id_seq;"},
        raise_for_status=True,
    )
    results = await resp.json()
    txid = results[0]["result"][0]["last_value"]
    sdk._test_start_txid = int(txid)

    yield txid

    sdk._test_start_txid = -1
    await aidbox.post(
        "/$psql",
        json={"query": "select drop_before_all({});".format(txid)},
        params={"execute": "true"},
        raise_for_status=True,
    )


@pytest.fixture
def sdk(client):
    return client.server.app["sdk"]


@pytest.fixture
def aidbox_client(client):
    return client.server.app["client"]


@pytest.fixture()
def aidbox_db(client):
    return client.server.app["db"]
