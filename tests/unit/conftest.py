import pytest


@pytest.fixture(scope="session", autouse=True)
def app():
    return
