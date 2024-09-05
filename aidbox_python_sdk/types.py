from typing import Any

from aiohttp import web
from typing_extensions import TypedDict

SDKOperationRequest = TypedDict(
    "SDKOperationRequest",
    {"app": web.Application, "params": dict, "route-params": dict, "resource": Any},
)


class SDKOperation(TypedDict):
    pass
