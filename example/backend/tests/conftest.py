from typing import Protocol

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient
from fhirpy import AsyncFHIRClient

from app import app_keys as ak

pytest_plugins = ["aidbox_python_sdk.pytest_plugin"]


class SafeDBFixture(Protocol):
    pass


@pytest.fixture()
def fhir_client(client: TestClient) -> AsyncFHIRClient:
    app: web.Application = client.server.app  # type: ignore

    return app[ak.fhir_client]
