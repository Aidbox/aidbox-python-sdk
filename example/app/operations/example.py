import fhirpy_types_r4b as r4b
from aidbox_python_sdk.types import SDKOperation, SDKOperationRequest
from aiohttp import web

from app import app_keys as ak
from app.sdk import sdk


@sdk.operation(["POST"], ["$example"])
async def example_op(_operation: SDKOperation, request: SDKOperationRequest) -> web.Response:
    fhir_client = request["app"][ak.fhir_client]

    await fhir_client.save(r4b.Patient(id="example"))
    patient = await fhir_client.get(r4b.Patient, "example")

    return web.json_response({"status": "ok", "patient": patient.model_dump()})

