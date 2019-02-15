import logging
from aiohttp import web

logger = logging.getLogger('aiohttp.access')
routes = web.RouteTableDef()


async def manifest(request):
    return web.json_response({'manifest': request.app['manifest']})


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
        'url': app['settings'].APP_URL,
        'secret': app['settings'].APP_INIT_CLIENT_SECRET,
    }

    async with app['client'].post(
            '{}/App/$init'.format(app['settings'].APP_INIT_URL),
            json=json) as resp:
        logger.info(resp.status)
        logger.info(await resp.text())


@routes.get('/init')
async def init(request):
    await init_aidbox(request.app)
    return web.json_response({})


@routes.post('/')
async def index(request):
    logger.info('New request {} {}'.format(request.method, request.url))
    json = await request.json()
    if 'type' in json and json['type'] in TYPES:
        logger.info(json['type'])
        return await TYPES[json['type']](request)
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
