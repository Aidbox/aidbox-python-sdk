import logging
import asyncio
import pytest

import fhirpy


async def test_default_timout_works(sdk, safe_db):
    response = await sdk.client.execute("$default-timeout", "GET")
    assert response == {"result": "success"}


async def test_custom_timout_applied(sdk, safe_db):
    with pytest.raises(fhirpy.base.exceptions.OperationOutcome) as timeout_exc:
        response = await sdk.client.execute("$custom-timeout", "GET")
    assert "idle timeout" in str(timeout_exc)
