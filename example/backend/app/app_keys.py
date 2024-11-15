from aidbox_python_sdk.app_keys import client, sdk, settings
from aiohttp import ClientSession, web
from fhirpy import AsyncFHIRClient

fhir_client: web.AppKey[AsyncFHIRClient] = web.AppKey("fhir_client", AsyncFHIRClient)
session = web.AppKey("session", ClientSession)

__all__ = ["fhir_client", "client", "sdk", "settings", "session"]
