import logging
from json import loads
from os import getenv
from aiohttp import web


logger = logging.getLogger('aiohttp.access')

MANIFEST = {
    'id': getenv('APP_ID'),
    'resourceType': 'App',
    'type': 'app',
    'apiVersion': 1,
    'endpoint': {
        'url': getenv('APP_URL'),
        'type': 'http-rpc',
        'secret': getenv('APP_SECRET'),
    },
    'subscriptions': {
        'User': {
            'handler': '/kek'
        }
    }
}


async def manifest(request):
    return web.json_response(MANIFEST)


async def log_request(request):
    logger.info(await request.text())
    return web.json_response({})


TYPES = {
    'manifest': manifest,
    'config': log_request,
    'operation': log_request,
    'subscription': log_request,
}


async def init_aidbox(app):
    json = {
        'url': getenv('APP_URL'),
        'secret': getenv('APP_INIT_CLIENT_SECRET'),
    }

    async with app['client'].post(
            '{}/App/$init'.format(getenv('APP_INIT_URL')),
            json=json) as resp:
        logger.info(resp.status)
        logger.info(await resp.text())


async def init(request):
    await init_aidbox(request.app)
    return web.json_response({})


async def T(request):
    text = await request.text()
    logger.info(type(text))
    logger.info(text)
    # json = loads(text)
    # if 'type' in json and json['type'] in TYPES:
    #     return await TYPES[json['type']](request)
    req = {
        'method': request.method,
        'url': str(request.url),
        'raw_path': request.raw_path,
        'headers': dict(request.headers),
        'json': await request.json(),
        'charset': request.charset,
    }
    logger.info(req)
    return web.json_response(req, status=200)
