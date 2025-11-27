import fhirpy_types_r4b as r4b
from fhirpy import AsyncFHIRClient

from tests.conftest import SafeDBFixture


async def test_database_isolation__1(fhir_client: AsyncFHIRClient, safe_db: SafeDBFixture) -> None:
    patients = await fhir_client.resources(r4b.Patient).fetch_all()
    assert len(patients) == 0

    await fhir_client.create(r4b.Patient())

    patients = await fhir_client.resources(r4b.Patient).fetch_all()
    assert len(patients) == 1


async def test_database_isolation__2(fhir_client: AsyncFHIRClient, safe_db: SafeDBFixture) -> None:
    patients = await fhir_client.resources(r4b.Patient).fetch_all()
    assert len(patients) == 0

    await fhir_client.create(r4b.Patient())
    await fhir_client.create(r4b.Patient())

    patients = await fhir_client.resources(r4b.Patient).fetch_all()
    assert len(patients) == 2  # noqa: PLR2004


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
