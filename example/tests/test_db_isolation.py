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
