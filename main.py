import asyncio
import logging
import time
from datetime import datetime

import coloredlogs
import sqlalchemy as sa
from aiohttp import web
from sqlalchemy.sql.expression import insert, select

from aidbox_python_sdk.handlers import routes
from aidbox_python_sdk.main import create_app as _create_app
from aidbox_python_sdk.sdk import SDK
from aidbox_python_sdk.settings import Settings

logger = logging.getLogger()
coloredlogs.install(level="DEBUG", fmt="%(asctime)s %(levelname)s %(message)s")

settings = Settings(**{})
resources = {
    "Client": {"SPA": {"secret": "123456", "grant_types": ["password"]}},
    "User": {
        "superadmin": {
            "email": "superadmin@example.com",
            "password": "12345678",
        }
    },
    "AccessPolicy": {"superadmin": {"engine": "json-schema", "schema": {"required": ["user"]}}},
}
seeds = {
    "Patient": {
        "dfaa8925-f32e-4687-8fd0-272844cff544": {
            "name": [
                {
                    "use": "official",
                    "family": "Hauck852",
                    "given": ["Alayna598"],
                    "prefix": ["Ms."],
                }
            ],
            "gender": "female",
        },
        "dfaa8925-f32e-4687-8fd0-272844cff545": {
            "name": [
                {
                    "use": "official",
                    "family": "Doe12",
                    "given": ["John46"],
                    "prefix": ["Ms."],
                }
            ]
        },
    },
    "Contract": {
        "e9a3ce1d-745d-4fe1-8e97-807a820e6151": {},
        "e9a3ce1d-745d-4fe1-8e97-807a820e6152": {},
        "e9a3ce1d-745d-4fe1-8e97-807a820e6153": {},
    },
}
sdk = SDK(settings, resources=resources, seeds=seeds)


def create_app():
    return _create_app(sdk)


@sdk.subscription("Appointment")
async def appointment_sub(event, request):
    """
    POST /Appointment
    """
    await asyncio.sleep(5)
    return await _appointment_sub(event, request)


async def _appointment_sub(event, request):
    participants = event["resource"]["participant"]
    patient_id = next(
        p["actor"]["id"] for p in participants if p["actor"]["resourceType"] == "Patient"
    )
    patient = await request.app["client"].resources("Patient").get(id=patient_id)
    patient_name = "{} {}".format(patient["name"][0]["given"][0], patient["name"][0]["family"])
    appointment_dates = "Start: {:%Y-%m-%d %H:%M}, end: {:%Y-%m-%d %H:%M}".format(
        datetime.fromisoformat(event["resource"]["start"]),
        datetime.fromisoformat(event["resource"]["end"]),
    )
    logging.info("*" * 40)
    if event["action"] == "create":
        logging.info("%s, new appointment was created.", patient_name)
        logging.info(appointment_dates)
    elif event["action"] == "update":
        if event["resource"]["status"] == "booked":
            logging.info("%s, appointment was updated.", patient_name)
            logging.info(appointment_dates)
        elif event["resource"]["status"] == "cancelled":
            logging.info("%s, appointment was cancelled.", patient_name)
    logging.debug("`Appointment` subscription handler")
    logging.debug("Event: %s", event)


@sdk.operation(
    methods=["POST", "PATCH"],
    path=["signup", "register", {"name": "date"}, {"name": "test"}],
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


@sdk.operation(methods=["GET"], path=["Patient", "$weekly-report"], public=True)
@sdk.operation(methods=["GET"], path=["Patient", "$daily-report"])
async def daily_patient_report(operation, request):
    """
    GET /Patient/$weekly-report
    GET /Patient/$daily-report
    """
    patients = request.app["client"].resources("Patient")
    async for p in patients:
        logging.debug(p.serialize())
    logging.debug("`daily_patient_report` operation handler")
    logging.debug("Operation data: %s", operation)
    logging.debug("Request: %s", request)
    return web.json_response({"type": "report", "success": "Ok", "msg": "Response from APP"})


@routes.get("/db_tests")
async def db_tests(request):
    db = request.app["db"]
    app = db.App.__table__
    app_res = {
        "type": "app",
        "resources": {
            "User": {},
        },
    }
    unique_id = f"abc{time.time()}"
    test_statements = [
        insert(app)
        .values(id=unique_id, txid=123, status="created", resource=app_res)
        .returning(app.c.id),
        app.update()
        .where(app.c.id == unique_id)
        .values(resource=app.c.resource.op("||")({"additional": "property"})),
        app.select().where(app.c.id == unique_id),
        app.select().where(app.c.status == "recreated"),
        select([app.c.resource["type"].label("app_type")]),
        app.select().where(app.c.resource["resources"].has_key("User")),
        select([app.c.id]).where(app.c.resource["type"].astext == "app"),
        select([sa.func.count(app.c.id)]).where(app.c.resource.contains({"type": "app"})),
        # TODO: got an error for this query.
        # select('*').where(app.c.resource['resources'].has_all(array(['User', 'Client']))),
    ]
    for statement in test_statements:
        result = await db.alchemy(statement)
        logging.debug("Result:\n%s", result)
    return web.json_response({})


@sdk.operation(
    ["POST"],
    ["Observation", "observation-custom-op"],
    compliance={
        "fhirCode": "observation-custom-op",
        "fhirUrl": "http://test.com",
        "fhirResource": ["Observation"],
    })
async def observation_custom_op(operation, request):
    return {"message": "Observation custom operation response"}
