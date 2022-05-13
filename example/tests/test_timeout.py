import logging
import asyncio
import pytest

import fhirpy


async def test_default_timout_works(sdk, safe_db):
    response = await sdk.client.execute("$default-timeout", "GET")
    assert response == {"result": "success"}


async def test_sleep_operation_fails(sdk, safe_db):
    with pytest.raises(fhirpy.base.exceptions.OperationOutcome) as timeout_exc:
        await sdk.client.execute("$sleep/2500", "GET")
    assert "idle timeout" in str(timeout_exc)


async def test_sleep_operation_succeeds(sdk, safe_db):
    response = await sdk.client.execute("$sleep/1", "GET")
    assert response == {"result": "success"}
