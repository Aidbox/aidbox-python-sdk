import asyncio
import pytest
import os
from yarl import URL
from aiohttp import ClientSession, BasicAuth, hdrs
from aiohttp.test_utils import TestServer, TestClient, BaseTestServer
from aiohttp.web import Application
from aiohttp.client import _RequestContextManager

from main import create_app as _create_app


@pytest.yield_fixture(scope="session")
def loop():  # type: ignore
    """Return an instance of the event loop."""
    loop = asyncio.get_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def aiohttp_client(loop):  # type: ignore
    """Factory to create a TestClient instance.
    aiohttp_client(app, **kwargs)
    aiohttp_client(server, **kwargs)
    aiohttp_client(raw_server, **kwargs)
    """
    clients = []

    async def go(__param, *, server_kwargs=None, **kwargs):  # type: ignore
        if isinstance(__param, Application):
            server_kwargs = server_kwargs or {}
            server = TestServer(__param, **server_kwargs)
            client = TestClient(server, **kwargs)
        elif isinstance(__param, BaseTestServer):
            client = TestClient(__param, **kwargs)
        else:
            raise ValueError("Unknown argument type: %r" % type(__param))

        await client.start_server()
        clients.append(client)
        return client

    yield go

    async def finalize():  # type: ignore
        while clients:
            await clients.pop().close()

    loop.run_until_complete(finalize())


async def start_app(aiohttp_client):
    app = await aiohttp_client(_create_app(),
                               server_kwargs={"host": "0.0.0.0", "port": 8081})
    await app.server.app['sdk'].is_ready
    return app


@pytest.fixture(scope="session")
def client(loop, aiohttp_client):
    """Instance of app's server and client"""
    return loop.run_until_complete(
        start_app(aiohttp_client)
    )


class CustomClient:
    def __init__(self,
                 base_url='http://127.0.0.1:8080',
                 loop=None,
                 **session_kwargs):
        self.base_url = URL(base_url)
        self._session = ClientSession(loop=loop,
                                      **session_kwargs)
        self._closed = False
        self._responses = []

    @property
    def session(self):
        return self._session
    
    def make_url(self, path):
        return self.base_url.with_path(path)

    async def request(self,
                method,
                path,
                **kwargs):
        resp = await self._session.request(
            method, self.make_url(path), **kwargs
        )
        # save it to close later
        self._responses.append(resp)
        return resp

    def get(self, path, **kwargs):
        return _RequestContextManager(
            self.request(hdrs.METH_GET, path, **kwargs)
        )

    def post(self, path, **kwargs):
        return _RequestContextManager(
            self.request(hdrs.METH_POST, path, **kwargs)
        )

    def options(self, path, **kwargs):
        return _RequestContextManager(
            self.request(hdrs.METH_OPTIONS, path, **kwargs)
        )

    def head(self, path, **kwargs):
        return _RequestContextManager(
            self.request(hdrs.METH_HEAD, path, **kwargs)
        )

    def put(self, path, **kwargs):
        return _RequestContextManager(
            self.request(hdrs.METH_PUT, path, **kwargs)
        )

    def patch(self, path, **kwargs):
        return _RequestContextManager(
            self.request(hdrs.METH_PATCH, path, **kwargs)
        )

    def delete(self, path, **kwargs):
        return _RequestContextManager(
            self.request(hdrs.METH_DELETE, path, **kwargs)
        )
        
    async def close(self) -> None:
        if not self._closed:
            for resp in self._responses:
                resp.close()
            await self._session.close()
            self._closed = True


@pytest.yield_fixture()
async def aidbox(client):
    """HTTP client for making requests to Aidbox"""
    app = client.server.app
    basic_auth = BasicAuth(
        login=app["settings"].APP_INIT_CLIENT_ID,
        password=app["settings"].APP_INIT_CLIENT_SECRET,
    )
    base_url = os.environ.get('AIDBOX_BASE_URL')
    session = CustomClient(base_url=base_url, **{'auth': basic_auth})
    yield session
    await session.close()
