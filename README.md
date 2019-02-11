aidbox-python-sdk
=================


1. Activate a python 3.6 environment `python3.6 -m venv env`
2. Set env variables and activate virtual environment `source activate_settings.sh` 
2. Install the required packages with `pip install -r requirements/base.txt -r requirements/dev.txt`
3. Make sure the app's settings are configured correctly (see `activate_settings.sh` and `aidbox_python_sdk/settings.py`). You can also
 use environment variables to define sensitive settings, eg. DB connection variables
4. You can then run your app during development with `adev runserver`.