import asyncio
import pytest
import logging
from aiohttp import ClientSession, BasicAuth
from aiohttp.test_utils import TestServer, TestClient, BaseTestServer
from aiohttp.web import Application

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
        await asyncio.sleep(5)
        return client

    yield go

    async def finalize():  # type: ignore
        logging.debug('finalize')
        while clients:
            await clients.pop().close()

    loop.run_until_complete(finalize())


@pytest.fixture(scope="session")
def cli(loop, aiohttp_client):
    return loop.run_until_complete(
        aiohttp_client(_create_app(), server_kwargs={"port": 8081})
    )


@pytest.yield_fixture()
async def aidbox_client(cli):
    app = cli.server.app
    basic_auth = BasicAuth(
        login=app["settings"].APP_INIT_CLIENT_ID,
        password=app["settings"].APP_INIT_CLIENT_SECRET,
    )
    session = ClientSession(auth=basic_auth)
    yield session
    await session.close()

