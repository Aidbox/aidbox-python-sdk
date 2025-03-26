from typing import Any

from aiohttp import web
from typing_extensions import TypedDict

class Compliance(TypedDict, total=True):
    fhirUrl: str
    fhirCode: str
    fhirResource: list[str]

SDKOperationRequest = TypedDict(
    "SDKOperationRequest",
    {"app": web.Application, "params": dict, "route-params": dict, "headers": dict, "resource": Any},
)


class SDKOperation(TypedDict):
    pass
