import logging
import asyncio
import os
from aiohttp import web
from fhirpy.base.exceptions import OperationOutcome

logger = logging.getLogger("aidbox_sdk")
routes = web.RouteTableDef()


async def subscription(request, data):
    logger.debug("Subscription handler: {}".format(data["handler"]))
    if "handler" not in data or "event" not in data:
        logger.error("`handler` and/or `event` param is missing, data: {}".format(data))
        raise web.HTTPBadRequest()
    handler = request.app["sdk"].get_subscription_handler(data["handler"])
    if not handler:
        logger.error("Subscription handler `{}` was not found".format(data["handler"]))
        raise web.HTTPNotFound()
    result = handler(data["event"], request)
    if asyncio.iscoroutine(result):
        asyncio.get_event_loop().create_task(result)
    return web.json_response({})


async def operation(request, data):
    logger.debug("Operation handler: %s", data["operation"]["id"])
    if "operation" not in data or "id" not in data["operation"]:
        logger.error(
            "`operation` or `operation[id]` param is missing, data: %s", data
        )
        raise web.HTTPBadRequest()
    handler = request.app["sdk"].get_operation_handler(data["operation"]["id"])
    if not handler:
        logger.error("Operation handler `%s` was not found", data["handler"])
        raise web.HTTPNotFound()
    try:
        result = handler(data["operation"], data["request"])
        if asyncio.iscoroutine(result):
            try:
                return await result
            except asyncio.CancelledError as err:
                logger.error("Aidbox timeout for %s", data["operation"])
                raise err

        return result
    except OperationOutcome as exc:
        return web.json_response(exc.resource, status=422)


TYPES = {
    "operation": operation,
    "subscription": subscription,
}


@routes.post("/aidbox")
async def dispatch(request):
    logger.debug("Dispatch new request {} {}".format(request.method, request.url))
    json = await request.json()
    if "type" in json and json["type"] in TYPES:
        logger.debug("Dispatch to `{}` handler".format(json["type"]))
        return await TYPES[json["type"]](request, json)
    req = {
        "method": request.method,
        "url": str(request.url),
        "raw_path": request.raw_path,
        "headers": dict(request.headers),
        "text": await request.text(),
        "charset": request.charset,
    }
    return web.json_response(req, status=200)


@routes.get("/health")
async def health_check(request):
    return web.json_response({"status": "OK"}, status=200)


@routes.get("/live")
async def live_health_check(request):
    return web.json_response({"status": "OK"}, status=200)
