from typing_extensions import TypedDict

from aidbox_python_sdk.aidboxpy import AsyncAidboxClient
from aidbox_python_sdk.db import DBProxy
from aidbox_python_sdk.sdk import SDK


class SDKOperationRequestApp(TypedDict):
    client: AsyncAidboxClient
    db: DBProxy
    sdk: SDK


SDKOperationRequest = TypedDict(
    "SDKOperationRequest", {"app": SDKOperationRequestApp, "route-params": dict, "resource": dict}
)
