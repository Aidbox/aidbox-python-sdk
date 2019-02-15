import logging
import asyncio
import json
from aiohttp import web

logger = logging.getLogger()
routes = web.RouteTableDef()


async def manifest(request):
    logger.info('app manifest: {}'.format(request.app['manifest'].build()))
    return web.json_response({'manifest': request.app['manifest'].build()})


async def subscription(request):
    data = await request.json()
    logger.info('subscription, handler: {}'.format(data['handler']))
    if 'handler' not in data or 'event' not in data:
        logger.error('`handler` and/or `event` param is missing, data: {}'.format(json.dumps(data)))
        raise web.HTTPBadRequest()
    handler = request.app['manifest'].get_subscription_handler(data['handler'])
    if not handler:
        logger.error('Subscription handler `{}` was not found'.format(data['handler']))
        raise web.HTTPNotFound()
    if asyncio.iscoroutine(handler):
        return await handler(data['event'])
    return handler(data['event'])


async def operation(request):
    pass


async def log_request(request):
    logger.info('log_request')
    return web.json_response({})


TYPES = {
    'manifest': manifest,
    'config': log_request,
    'operation': operation,
    'subscription': subscription,
}


@routes.get('/init')
async def init(request):
    await request.app['init_aidbox_app'](request.app)
    return web.json_response({})


@routes.post('/')
async def dispatch(request):
    logger.info('Dispatch new request {} {}'.format(request.method, request.url))
    req = {
        'method': request.method,
        'url': str(request.url),
        'raw_path': request.raw_path,
        'headers': dict(request.headers),
        'text': await request.text(),
        'charset': request.charset,
    }
    logger.info(req)
    json = await request.json()
    if 'type' in json and json['type'] in TYPES:
        logger.info('Dispatch to `{}` handler'.format(json['type']))
        return await TYPES[json['type']](request)
    return web.json_response(req, status=200)
