import logging
import asyncio
from aiohttp import web

logger = logging.getLogger('aidbox_sdk')
routes = web.RouteTableDef()


async def manifest(request, data):
    logger.info('app manifest: {}'.format(request.app['sdk'].build_manifest()))
    return web.json_response({'manifest': request.app['sdk'].build_manifest()})


async def subscription(request, data):
    logger.debug('Subscription handler: {}'.format(data['handler']))
    if 'handler' not in data or 'event' not in data:
        logger.error('`handler` and/or `event` param is missing, data: {}'.format(data))
        raise web.HTTPBadRequest()
    handler = request.app['sdk'].get_subscription_handler(data['handler'])
    if not handler:
        logger.error('Subscription handler `{}` was not found'.format(data['handler']))
        raise web.HTTPNotFound()
    result = handler(data['event'])
    if asyncio.iscoroutine(result):
        asyncio.get_event_loop().create_task(result)
    return web.json_response({})


async def operation(request, data):
    logger.debug(data)
    logger.debug('Operation handler: {}'.format(data['operation']['id']))
    if 'operation' not in data or 'id' not in data['operation']:
        logger.error('`operation` or `operation[id]` param is missing, data: {}'.format(data))
        raise web.HTTPBadRequest()
    handler = request.app['sdk'].get_operation_handler(data['operation']['id'])
    if not handler:
        logger.error('Operation handler `{}` was not found'.format(data['handler']))
        raise web.HTTPNotFound()
    result = handler(data['operation'], data['request'])
    if asyncio.iscoroutine(result):
        return await result
    return result


async def log_request(request, data):
    logger.info('log_request {} {}'.format(request, data))
    return web.json_response({})


async def config(request, config):
    request.app['sdk'].init_client(config)
    return web.json_response({})


TYPES = {
    'manifest': manifest,
    'config': config,
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
    json = await request.json()
    if 'type' in json and json['type'] in TYPES:
        logger.info('Dispatch to `{}` handler'.format(json['type']))
        return await TYPES[json['type']](request, json)
    req = {
        'method': request.method,
        'url': str(request.url),
        'raw_path': request.raw_path,
        'headers': dict(request.headers),
        'text': await request.text(),
        'charset': request.charset,
    }
    logger.info(req)
    return web.json_response(req, status=200)


@routes.get('/')
async def health_check(request):
    return web.json_response({'status': 'OK'}, status=200)
