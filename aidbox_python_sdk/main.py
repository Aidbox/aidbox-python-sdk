import logging
import asyncio
from pathlib import Path
from aiohttp import web, ClientSession, BasicAuth, client_exceptions

from .handlers import routes

logger = logging.getLogger('aidbox_sdk')
THIS_DIR = Path(__file__).parent
BASE_DIR = THIS_DIR.parent


def setup_routes(app):
    app.add_routes(routes)


async def init_aidbox(app):
    json = {
        'url': app['settings'].APP_URL,
        'secret': app['settings'].APP_INIT_CLIENT_SECRET,
    }
    try:
        async with app['client'].post(
                '{}/App/$init'.format(app['settings'].APP_INIT_URL),
                json=json) as resp:
            logger.info(resp.status)
            logger.info(await resp.text())
    except (client_exceptions.ServerDisconnectedError, client_exceptions.ClientConnectionError):
        logger.error('Aidbox address is unreachable {}'.format(app['settings'].APP_INIT_URL))
        logger.error('Aidbox app init stopped')


async def wait_and_init_aidbox(app):
    while 1:
        try:
            address = 'http://{}'.format(app['settings'].APP_URL)
            logger.info("Check awailability of {}".format(address)
            async with app['client'].get(address):
                pass
            break
        except (client_exceptions.InvalidURL, client_exceptions.ClientConnectionError):
            await asyncio.sleep(2)
    await app['sdk'].db.create_all_mappings()
    await init_aidbox(app)


async def on_startup(app):
    basic_auth = BasicAuth(
        login=app['settings'].APP_INIT_CLIENT_ID,
        password=app['settings'].APP_INIT_CLIENT_SECRET)
    app['client'] = ClientSession(auth=basic_auth)
    app['sdk'].db.set_client(app['client'])
    asyncio.get_event_loop().create_task(wait_and_init_aidbox(app))


async def on_cleanup(app):
    await app['client'].close()


async def on_shutdown(app):
    if not app['client'].closed:
        await app['client'].close()


async def create_app(settings, sdk, debug=False):
    app = web.Application(debug=debug)
    app.on_startup.append(on_startup)
    app.on_cleanup.append(on_cleanup)
    app.on_shutdown.append(on_shutdown)
    app.update(
        name='aidbox-python-sdk',
        settings=settings,
        sdk=sdk,
        init_aidbox_app=init_aidbox,
        livereload=True
    )
    setup_routes(app)
    return app
