import asyncio
import logging
from unittest import mock

import pytest

import main


@pytest.mark.asyncio
async def test_operation_with_compliance_params(client):
    sdk = client.server.app["sdk"]

    compliance = {
        "fhirCode": "observation-custom-op",
        "fhirUrl": "http://test.com",
        "fhirResource": ["Observation"],
    }

    @sdk.operation(["POST"], ["Observation", "observation-custom-op"], compliance=compliance)
    async def observation_custom_op(operation, request):
        return {"message": "Observation custom operation response"}


    operation_id = "POST.tests.test_sdk.observation_custom_op.Observation_observation-custom-op"

    assert operation_id in sdk._operations

    assert sdk._operations[operation_id]["fhirCode"] == "observation-custom-op"
    assert sdk._operations[operation_id]["fhirUrl"] == "http://test.com"
    assert sdk._operations[operation_id]["fhirResource"] == ["Observation"]

    handler = sdk.get_operation_handler(operation_id)
    assert handler is not None

    response = await handler({}, {})
    assert response == {"message": "Observation custom operation response"}


@pytest.mark.asyncio()
async def test_health_check(client):
    resp = await client.get("/health")
    assert resp.status == 200
    json = await resp.json()
    assert json == {"status": "OK"}


@pytest.mark.asyncio()
async def test_live_health_check(client):
    resp = await client.get("/live")
    assert resp.status == 200
    json = await resp.json()
    assert json == {"status": "OK"}


@pytest.mark.skip()
async def test_signup_reg_op(client, aidbox):
    resp = await aidbox.post("signup/register/21.02.19/testvalue")
    assert resp.status == 200
    json = await resp.json()
    assert json == {
        "success": "Ok",
        "request": {"date": "21.02.19", "test": "testvalue"},
    }


@pytest.mark.skip()
async def test_appointment_sub(client, aidbox):
    with mock.patch.object(main, "_appointment_sub") as appointment_sub:
        f = asyncio.Future()
        f.set_result("")
        appointment_sub.return_value = f
        sdk = client.server.app["sdk"]
        was_appointment_sub_triggered = sdk.was_subscription_triggered("Appointment")
        resp = await aidbox.post(
            "Appointment",
            json={
                "status": "proposed",
                "participant": [{"status": "accepted"}],
                "resourceType": "Appointment",
            },
        )
        assert resp.status == 201
        await was_appointment_sub_triggered
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


@pytest.mark.asyncio()
async def test_database_isolation__1(aidbox_client, safe_db):
    patients = await aidbox_client.resources("Patient").fetch_all()
    assert len(patients) == 2

    patient = aidbox_client.resource("Patient")
    await patient.save()

    patients = await aidbox_client.resources("Patient").fetch_all()
    assert len(patients) == 3


@pytest.mark.asyncio()
async def test_database_isolation__2(aidbox_client, safe_db):
    patients = await aidbox_client.resources("Patient").fetch_all()
    assert len(patients) == 2

    patient = aidbox_client.resource("Patient")
    await patient.save()

    patient = aidbox_client.resource("Patient")
    await patient.save()

    patients = await aidbox_client.resources("Patient").fetch_all()
    assert len(patients) == 4
