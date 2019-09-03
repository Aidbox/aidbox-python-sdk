import asyncio
import pytest
import logging
from aiohttp import web, ClientSession, BasicAuth
from unittest import mock

import main


# async def test_hello(aiohttp_client):
#     client = await aiohttp_client(await _create_app())
#     resp = await client.get('/')
#     assert resp.status == 200
#     json = await resp.json()
#     assert json == {"status": "OK"}


async def test_signup_reg_op(cli, aidbox_client):
    resp = await aidbox_client.post(
        "http://localhost:8080/signup/register/21.02.19/testvalue"
    )
    assert resp.status == 200
    json = await resp.json()
    assert json == {
        "success": "Ok",
        "request": {"date": "21.02.19", "test": "testvalue"},
    }


async def test_appointment_sub(cli, aidbox_client):
    with mock.patch.object(main, "_appointment_sub") as appointment_sub:
        f = asyncio.Future()
        f.set_result("")
        appointment_sub.return_value = f
        resp = await aidbox_client.post(
            "http://localhost:8080/Appointment",
            json={
                "status": "proposed",
                "participant": [{"status": "accepted"}],
                "resourceType": "Appointment",
            },
        )
        assert resp.status == 201
        await asyncio.sleep(5)
        event = appointment_sub.call_args_list[0][0][0]
        logging.debug("event: %s", event)
        expected = {
            "resource": {
                "status": "proposed",
                "participant": [{"status": "accepted"}],
                "resourceType": "Appointment",
            },
            "action": "create",
        }
        assert expected["resource"].items() <= event["resource"].items()
