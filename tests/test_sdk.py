import asyncio
import logging
from unittest import mock

import pytest
from fhirpathpy import evaluate

import main


@pytest.mark.skip("Skipped because of regression in Aidbox 2510")
@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("expression", "expected"),
    [
        (
            "CapabilityStatement.rest.operation.where(definition='http://test.com').count()",
            1,
        ),
        (
            "CapabilityStatement.rest.operation.where(definition='http://test.com').first().name",
            "observation-custom-op",
        ),
        (
            "CapabilityStatement.rest.resource.where(type='Observation').operation.where(definition='http://test.com').count()",
            1,
        ),
        (
            "CapabilityStatement.rest.resource.where(type='Observation').operation.where(definition='http://test.com').first().name",
            "observation-custom-op",
        ),
    ],
)
async def test_operation_with_compliance_params(aidbox_client, expression, expected):
    response = await aidbox_client.execute("fhir/metadata", method="GET")
    assert evaluate(response, expression, {})[0] == expected


@pytest.mark.asyncio
async def test_health_check(client):
    resp = await client.get("/health")
    assert resp.status == 200
    json = await resp.json()
    assert json == {"status": "OK"}


@pytest.mark.asyncio
async def test_live_health_check(client):
    resp = await client.get("/live")
    assert resp.status == 200
    json = await resp.json()
    assert json == {"status": "OK"}


@pytest.mark.asyncio
async def test_signup_reg_op(aidbox_client):
    json = await aidbox_client.execute("signup/register/21.02.19/testvalue")
    assert json == {
        "success": "Ok",
        "request": {"date": "21.02.19", "test": "testvalue"},
    }


@pytest.mark.asyncio
async def test_appointment_sub(sdk, aidbox_client, safe_db):
    with mock.patch.object(main, "_appointment_sub") as appointment_sub:
        f = asyncio.Future()
        f.set_result("")
        appointment_sub.return_value = f
        was_appointment_sub_triggered = sdk.was_subscription_triggered("Appointment")
        resource = aidbox_client.resource(
            "Appointment",
            **{
                "status": "proposed",
                "participant": [{"status": "accepted"}],
            },
        )
        await resource.save()
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


@pytest.mark.asyncio
async def test_database_isolation__1(aidbox_client, safe_db):
    patients = await aidbox_client.resources("Patient").fetch_all()
    assert len(patients) == 2

    patient = aidbox_client.resource("Patient")
    await patient.save()

    patients = await aidbox_client.resources("Patient").fetch_all()
    assert len(patients) == 3


@pytest.mark.asyncio
async def test_database_isolation__2(aidbox_client, safe_db):
    patients = await aidbox_client.resources("Patient").fetch_all()
    assert len(patients) == 2

    patient = aidbox_client.resource("Patient")
    await patient.save()

    patient = aidbox_client.resource("Patient")
    await patient.save()

    patients = await aidbox_client.resources("Patient").fetch_all()
    assert len(patients) == 4


@pytest.mark.asyncio
async def test_database_isolation_with_history_in_name__1(aidbox_client, safe_db):
    resources = await aidbox_client.resources("FamilyMemberHistory").fetch_all()
    assert len(resources) == 0

    resource = aidbox_client.resource(
        "FamilyMemberHistory",
        status="completed",
        patient={
            "identifier": {"system": "http://example.org/test-patients", "value": "test-patient-1"}
        },
        relationship={
            "coding": [
                {"system": "http://terminology.hl7.org/CodeSystem/v3-RoleCode", "code": "FTH"}
            ]
        },
    )
    await resource.save()

    resources = await aidbox_client.resources("FamilyMemberHistory").fetch_all()
    assert len(resources) == 1


@pytest.mark.asyncio
async def test_database_isolation_with_history_in_name__2(aidbox_client, safe_db):
    resources = await aidbox_client.resources("FamilyMemberHistory").fetch_all()
    assert len(resources) == 0

    resource1 = aidbox_client.resource(
        "FamilyMemberHistory",
        status="completed",
        patient={
            "identifier": {"system": "http://example.org/test-patients", "value": "test-patient-1"}
        },
        relationship={
            "coding": [
                {"system": "http://terminology.hl7.org/CodeSystem/v3-RoleCode", "code": "FTH"}
            ]
        },
    )
    await resource1.save()

    resource2 = aidbox_client.resource(
        "FamilyMemberHistory",
        status="completed",
        patient={
            "identifier": {"system": "http://example.org/test-patients", "value": "test-patient-2"}
        },
        relationship={
            "coding": [
                {"system": "http://terminology.hl7.org/CodeSystem/v3-RoleCode", "code": "MTH"}
            ]
        },
    )
    await resource2.save()

    resources = await aidbox_client.resources("FamilyMemberHistory").fetch_all()
    assert len(resources) == 2
