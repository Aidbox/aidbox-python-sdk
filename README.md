[![build status](https://github.com/Aidbox/aidbox-python-sdk/actions/workflows/build.yaml/badge.svg)](https://github.com/Aidbox/aidbox-python-sdk/actions/workflows/build.yaml)
[![pypi](https://img.shields.io/pypi/v/aidbox-python-sdk.svg)](https://pypi.org/project/aidbox-python-sdk/)
[![Supported Python version](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/release/python-390/)

# aidbox-python-sdk

1. Create a python 3.9+ environment `pyenv `
2. Set env variables and activate virtual environment `source activate_settings.sh`
2. Install the required packages with `pipenv install --dev`
3. Make sure the app's settings are configured correctly (see `activate_settings.sh` and `aidbox_python_sdk/settings.py`). You can also
 use environment variables to define sensitive settings, eg. DB connection variables (see example `.env-ptl`)
4. You can then run example with `python example.py`.

# Getting started

## Minimal application

main.py
```python
from aidbox_python_sdk.main import create_app as _create_app
from aidbox_python_sdk.settings import Settings
from aidbox_python_sdk.sdk import SDK


settings = Settings(**{})
sdk = SDK(settings, resources={}, seeds={})


def create_app():
    app = await _create_app(SDK)
    return app


async def create_gunicorn_app() -> web.Application:
    return create_app()
```

## Register handler for operation
```python
import logging
from aiohttp import web
from aidbox_python_sdk.types import SDKOperation, SDKOperationRequest

from yourappfolder import sdk 


@sdk.operation(
    methods=["POST", "PATCH"],
    path=["signup", "register", {"name": "date"}, {"name": "test"}],
    timeout=60000  ## Optional parameter to set a custom timeout for operation in milliseconds
)
def signup_register_op(_operation: SDKOperation, request: SDKOperationRequest):
    """
    POST /signup/register/21.02.19/testvalue
    PATCH /signup/register/22.02.19/patchtestvalue
    """
    logging.debug("`signup_register_op` operation handler")
    logging.debug("Operation data: %s", operation)
    logging.debug("Request: %s", request)
    return web.json_response({"success": "Ok", "request": request["route-params"]})

```

## Usage of AppKeys

To access Aidbox Client, SDK, settings, DB Proxy the `app` (`web.Application`) is extended by default with the following app keys that are defined in `aidbox_python_sdk.app_keys` module:

```python
from aidbox_python_sdk import app_keys as ak
from aidbox_python_sdk.types import SDKOperation, SDKOperationRequest

@sdk.operation(["POST"], ["example"])
async def update_organization_op(_operation: SDKOperation, request: SDKOperationRequest):
    app = request.app
    client = app[ak.client] # AsyncAidboxClient
    sdk = app[ak.sdk] # SDK
    settings = app[ak.settings] # Settings
    db = app[ak.db] # DBProxy
    return web.json_response()
```

## Usage of FHIR Client

FHIR Client is not plugged in by default, however, to use it you can extend the app by adding new AppKey

app/app_keys.py
```python
from fhirpy import AsyncFHIRClient

fhir_client: web.AppKey[AsyncFHIRClient] = web.AppKey("fhir_client", AsyncFHIRClient)
```

main.py
```python
from collections.abc import AsyncGenerator

from aidbox_python_sdk.main import create_app as _create_app
from aidbox_python_sdk.settings import Settings
from aidbox_python_sdk.sdk import SDK
from aiohttp import BasicAuth, web
from fhirpy import AsyncFHIRClient

from app import app_keys as ak

settings = Settings(**{})
sdk = SDK(settings, resources={}, seeds={)

def create_app():
    app = await _create_app(SDK)
    app.cleanup_ctx.append(fhir_clients_ctx)
    return app


async def create_gunicorn_app() -> web.Application:
    return create_app()


async def fhir_clients_ctx(app: web.Application) -> AsyncGenerator[None, None]:
    app[ak.fhir_client] = await init_fhir_client(app[ak.settings], "/fhir")

    yield


async def init_fhir_client(settings: Settings, prefix: str = "") -> AsyncFHIRClient:
    basic_auth = BasicAuth(
        login=settings.APP_INIT_CLIENT_ID,
        password=settings.APP_INIT_CLIENT_SECRET,
    )

    return AsyncFHIRClient(
        f"{settings.APP_INIT_URL}{prefix}",
        authorization=basic_auth.encode(),
        dump_resource=lambda x: x.model_dump(),
    )
```

After that, you can use `app[ak.fhir_client]` that has the type `AsyncFHIRClient` everywhere where the app is available.


## Usage of request_schema
```python
from aidbox_python_sdk.types import SDKOperation, SDKOperationRequest

schema = {
    "required": ["params", "resource"],
    "properties": {
        "params": {
            "type": "object",
            "required": ["abc", "location"],
            "properties": {"abc": {"type": "string"}, "location": {"type": "string"}},
            "additionalProperties": False,
        },
        "resource": {
            "type": "object",
            "required": ["organizationType", "employeesCount"],
            "properties": {
                "organizationType": {"type": "string", "enum": ["profit", "non-profit"]},
                "employeesCount": {"type": "number"},
            },
            "additionalProperties": False,
        },
    },
}


@sdk.operation(["POST"], ["Organization", {"name": "id"}, "$update"], request_schema=schema)
async def update_organization_op(_operation: SDKOperation, request: SDKOperationRequest):
    location = request["params"]["location"]
    return web.json_response({"location": location})
```

### Valid request example
```shell
POST /Organization/org-1/$update?abc=xyz&location=us

organizationType: non-profit
employeesCount: 10
```


