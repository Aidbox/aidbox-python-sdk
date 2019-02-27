import sqlalchemy as sa
import logging
import coloredlogs
import time
from aiohttp import web
from datetime import datetime
from sqlalchemy.sql.expression import select, insert

from aidbox_python_sdk.main import create_app as _create_app
from aidbox_python_sdk.settings import Settings
from aidbox_python_sdk.sdk import SDK
from aidbox_python_sdk.handlers import routes


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
sdk = SDK(settings, resources)


async def create_app():
    return await _create_app(settings, sdk, debug=True)


@sdk.subscription('Appointment')
async def appointment_sub(event):
    """
    POST /Appointment
    """
    participants = event['resource']['participant']
    patient_id = next(p['actor']['id'] for p in participants if p['actor']['resourceType'] == 'Patient')
    patient = sdk.client.resources('Patient').get(id=patient_id)
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


@sdk.operation(methods=['POST', 'PATCH'], path=['signup', 'register', {"name": "date"}, {"name": "test"}])
def signup_register_op(operation, request):
    """
    POST /signup/register/21.02.19/testvalue
    PATCH /signup/register/22.02.19/patchtestvalue
    """
    logging.debug('`signup_register_op` operation handler')
    logging.debug('Operation data: {}'.format(operation))
    logging.debug('Request: {}'.format(request))
    return web.json_response({'success': 'Ok', 'request': request['route-params']})


@sdk.operation(methods=['GET'], path=['Patient', '$weekly-report'], public=True)
@sdk.operation(methods=['GET'], path=['Patient', '$daily-report'])
async def daily_patient_report(operation, request):
    """
    GET /Patient/$weekly-report
    GET /Patient/$daily-report
    """
    logging.debug('`daily_patient_report` operation handler')
    logging.debug('Operation data: {}'.format(operation))
    logging.debug('Request: {}'.format(request))
    return web.json_response({'type': 'report', 'success': 'Ok', 'msg': 'Response from APP'})


@routes.get('/db_tests')
async def db_tests(request):
    db = sdk.db
    app = db.App.__table__
    app_res = {
        'type': 'app',
        'resources': {
            'User': {},
        }
    }
    unique_id = 'abc{}'.format(time.time())
    test_statements = [
        insert(app).values(id=unique_id, txid=123, status='created', resource=app_res).returning(app.c.id),
        app.update().where(app.c.id == unique_id).values(resource=app.c.resource.op('||')({'additional': 'property'})),
        app.select().where(app.c.id == unique_id),
        app.select().where(app.c.status == 'recreated'),
        select([app.c.resource['type'].label('app_type')]),
        app.select().where(app.c.resource['resources'].has_key('User')),
        select([app.c.id]).where(app.c.resource['type'].astext == 'app'),
        select([sa.func.count(app.c.id)]).where(app.c.resource.contains({"type": "app"})),
        # TODO: got an error for this query.
        # select('*').where(app.c.resource['resources'].has_all(array(['User', 'Client']))),
    ]
    for statement in test_statements:
        query = await db.compile_statement(statement)
        logging.debug('Builded query:\n{}'.format(query))
        result = await db.make_query(query)
        logging.debug('Result:\n{}'.format(result))
    return web.json_response({})
