import logging
import coloredlogs
from aiohttp import web
from datetime import datetime
from aidbox_python_sdk.main import create_app as _create_app
from aidbox_python_sdk.settings import Settings
from aidbox_python_sdk.manifest import Manifest

coloredlogs.install(level='DEBUG', fmt='%(asctime)s %(levelname)s %(message)s')

settings = Settings(**{})
resources = {
    'Client': {
        'SPA': {
            'secret': '123456',
            'grant_types': [
                'password'
            ]
        }
    },
    'User': {
        'superadmin': {
            'email': 'superadmin@example.com',
            'password': '12345678',
        }
    },
    'AccessPolicy': {
        'superadmin': {
            'engine': 'json-schema',
            'schema': {'required': ['user']}
        }
    }

}
manifest = Manifest(settings, resources)


async def create_app():
    return await _create_app(settings, manifest, debug=True)


@manifest.subscription('Appointment')
async def appointment_sub(event):
    """
    POST /Appointment
    """
    participants = event['resource']['participant']
    patient_id = next(p['actor']['id'] for p in participants if p['actor']['resourceType'] == 'Patient')
    patient = manifest.client.resources('Patient').get(id=patient_id)
    patient_name = '{} {}'.format(patient['name'][0]['given'][0], patient['name'][0]['family'])
    appointment_dates = 'Start: {:%Y-%m-%d %H:%M}, end: {:%Y-%m-%d %H:%M}'.format(
        datetime.fromisoformat(event['resource']['start']),
        datetime.fromisoformat(event['resource']['end'])
    )
    logging.info('*' * 40)
    if event['action'] == 'create':
        logging.info('{}, new appointment was created.'.format(patient_name))
        logging.info(appointment_dates)
    elif event['action'] == 'update':
        if event['resource']['status'] == 'booked':
            logging.info('{}, appointment was updated.'.format(patient_name))
            logging.info(appointment_dates)
        elif event['resource']['status'] == 'cancelled':
            logging.info('{}, appointment was cancelled.'.format(patient_name))
    logging.debug('`Appointment` subscription handler')
    logging.debug('Event: {}'.format(event))


@manifest.operation(methods=['POST', 'PATCH'], path=['signup', 'register', {"name": "date"}, {"name": "test"}])
def signup_register_op(operation, request):
    """
    POST /signup/register/21.02.19/testvalue
    PATCH /signup/register/22.02.19/patchtestvalue
    """
    logging.debug('`signup_register_op` operation handler')
    logging.debug('Operation data: {}'.format(operation))
    logging.debug('Request: {}'.format(request))
    return web.json_response({'success': 'Ok', 'request': request['route-params']})


@manifest.operation(methods=['GET'], path=['Patient', '$weekly-report'], public=True)
@manifest.operation(methods=['GET'], path=['Patient', '$daily-report'])
async def daily_patient_report(operation, request):
    """
    GET /Patient/$weekly-report
    GET /Patient/$daily-report
    """
    logging.debug('`daily_patient_report` operation handler')
    logging.debug('Operation data: {}'.format(operation))
    logging.debug('Request: {}'.format(request))
    return web.json_response({'type': 'report', 'success': 'Ok', 'msg': 'Response from APP'})
