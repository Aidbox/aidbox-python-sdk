import fhirpy_types_r4b as r4b
from fhirpy import AsyncFHIRClient
from fhirpy.base import ResourceProtocol
from typing_extensions import TypeVar

TResource = TypeVar("TResource")


def make_reference_str(resource: ResourceProtocol) -> str:
    assert resource.id, "Field `id` must be presented"
    return f"{resource.resourceType}/{resource.id}"


def to_reference(resource: ResourceProtocol) -> r4b.Reference:
    return r4b.Reference(reference=make_reference_str(resource))


async def to_resource(
    client: AsyncFHIRClient, resource_type: type[TResource], reference: r4b.Reference
) -> TResource:
    assert reference.reference, "Field `reference` must be presented"
    resource_dict = await client.get(reference.reference)

    return resource_type(**resource_dict)


def get_resource_type(reference: r4b.Reference) -> str:
    assert reference.reference

    return reference.reference.split("/")[0]
