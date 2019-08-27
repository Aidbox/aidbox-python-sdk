# aidbox-python-sdk

1. Create a python 3.6 environment `python3.6 -m venv env`
2. Set env variables and activate virtual environment `source activate_settings.sh` 
2. Install the required packages with `pip install -r requirements/base.txt -r requirements/dev.txt`
3. Make sure the app's settings are configured correctly (see `activate_settings.sh` and `aidbox_python_sdk/settings.py`). You can also
 use environment variables to define sensitive settings, eg. DB connection variables (see example `.env-ptl`)
4. You can then run example with `python example.py`.

# Getting started
## Minimal application
```Python
from aidbox_python_sdk.main import create_app as _create_app
from aidbox_python_sdk.settings import Settings
from aidbox_python_sdk.sdk import SDK

settings = Settings(**{})
sdk = SDK(settings, resources=resources, seeds=seeds)

async def create_app():
    return await _create_app(settings, sdk, debug=True)

```
