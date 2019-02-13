import logging
from os import getenv
from aiohttp import web

logger = logging.getLogger('aiohttp.access')

manifest = {
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

    logger.info(manifest)
    async with app['client'].post(
            '{}/App'.format(getenv('APP_INIT_URL')),
            json=manifest) as resp:
        logger.info(resp.status)
        logger.info(await resp.text())



async def index(request):
    req = {
        'method': request.method,
        'url': str(request.url),
        'raw_path': request.raw_path,
        'headers': dict(request.headers),
        'json': await request.text(),
    }
    logger.info(req)
    return web.json_response(req)
