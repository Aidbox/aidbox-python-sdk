# aidbox-python-sdk

1. Create a python 3.8+ environment `pyenv `
2. Set env variables and activate virtual environment `source activate_settings.sh`
2. Install the required packages with `pipenv install --dev`
3. Make sure the app's settings are configured correctly (see `activate_settings.sh` and `aidbox_python_sdk/settings.py`). You can also
 use environment variables to define sensitive settings, eg. DB connection variables (see example `.env-ptl`)
4. You can then run example with `python example.py`.

Add `APP_FAST_START_MODE=TRUE` to env_tests for fast start mode.

# Getting started
## Minimal application
```Python
from aidbox_python_sdk.main import create_app as _create_app
from aidbox_python_sdk.settings import Settings
from aidbox_python_sdk.sdk import SDK

settings = Settings(**{})
sdk = SDK(settings, resources=resources, seeds=seeds)

async def create_app():
    return await _create_app(sdk)

```

## Register handler for operation
```Python
import logging
from aiohttp import web

from yourappfolder import sdk 


@sdk.operation(
    methods=["POST", "PATCH"],
    path=["signup", "register", {"name": "date"}, {"name": "test"}],
    timeout=60000  ## Optional parameter to set a custom timeout for operation in milliseconds
)
def signup_register_op(operation, request):
    """
    POST /signup/register/21.02.19/testvalue
    PATCH /signup/register/22.02.19/patchtestvalue
    """
    logging.debug("`signup_register_op` operation handler")
    logging.debug("Operation data: %s", operation)
    logging.debug("Request: %s", request)
    return web.json_response({"success": "Ok", "request": request["route-params"]})

```

## Validate request
```Python
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
async def update_organization_handler(operation, request):
    location = request["params"]["location"]
    return web.json_response({"location": location})
```
### Valid request example
```shell
POST /Organization/org-1/$update?abc=xyz&location=us

organizationType: non-profit
employeesCount: 10
```
