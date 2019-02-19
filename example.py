import logging
import coloredlogs
from aiohttp import web

from aidbox_python_sdk.main import run_standalone_app
from aidbox_python_sdk.settings import Settings
from aidbox_python_sdk.manifest import Manifest

coloredlogs.install(level='DEBUG', fmt='%(asctime)s %(levelname)s %(message)s')

settings = Settings(**{})
manifest = Manifest(settings)


def main():
    logging.info('Started')
    run_standalone_app(settings, manifest, debug=True)


"""
Test REST requests for subs and ops:
POST /User
POST /Contract
POST /Patient

POST /signup/register?param1=123&param2=foo
GET /Patient/$daily-report?param=papam
POST /User/$register
"""


@manifest.subscription('Contract')
@manifest.subscription('User')
async def user_and_contract_sub(event):
    logging.debug('`User` and `Contract` subscription handler')
    logging.debug('Event: {}'.format(event))

@manifest.subscription(entity='Patient')
def patient_sub(event):
    logging.debug('`Patient` subscription handler')
    logging.debug('Event: {}'.format(event))

@manifest.operation(method='POST', path=['signup', 'register', {"name": "date"}, {"name": "test"}])
def signup_register_op(operation, request):
    logging.debug('`signup_register_op` operation handler')
    logging.debug('Operation data: {}'.format(operation))
    logging.debug('Request: {}'.format(request))
    return web.json_response({"success": "Ok"})


@manifest.operation(method='GET', path=['Patient', '$daily-report'])
async def daily_patient_report(operation, request):
    logging.debug('`daily_patient_report` operation handler')
    logging.debug('Operation data: {}'.format(operation))
    logging.debug('Request: {}'.format(request))
    return web.json_response({})


@manifest.operation(method='POST', path=['User', '$register'])
async def register_user(operation, request):
    logging.debug('`register_user` operation handler')
    logging.debug('Operation data: {}'.format(operation))
    logging.debug('Request: {}'.format(request))
    return web.json_response({})


if __name__ == '__main__':
    main()
