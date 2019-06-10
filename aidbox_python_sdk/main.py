import logging
import sys
import errno

from pathlib import Path
from aiohttp import web, ClientSession, BasicAuth, client_exceptions
import asyncio

from .handlers import routes

logger = logging.getLogger('aidbox_sdk')
THIS_DIR = Path(__file__).parent
BASE_DIR = THIS_DIR.parent


def setup_routes(app):
    app.add_routes(routes)


async def init_aidbox(app):
    try:
        json = {
            'url': app['settings'].APP_URL,
            'secret': app['settings'].APP_INIT_CLIENT_SECRET,
        }
        async with app['init_http_client'].post(
                '{}/App/$init'.format(app['settings'].APP_INIT_URL),
                json=json
        ) as resp:
            if 200 <= resp.status < 300:
                logger.info('Initializing Aidbox app...')
            else:
                logger.error(
                    'Aidbox app initialized failed. '
                    'Response from Aidbox: {0} {1}'.format(
                        resp.status, await resp.text()))
                sys.exit(errno.EINTR)
    except (client_exceptions.ServerDisconnectedError,
            client_exceptions.ClientConnectionError):
        logger.error('Aidbox address is unreachable {}'.format(
            app['settings'].APP_INIT_URL))
        sys.exit(errno.EINTR)


async def wait_and_init_aidbox(app):
    address = app['settings'].APP_URL
    logger.debug("Check availability of {}".format(address))
    while 1:
        try:
            async with app['init_http_client'].get(address, timeout=5):
                pass
            break
        except (client_exceptions.InvalidURL,
                client_exceptions.ClientConnectionError):
            await asyncio.sleep(2)
    await init_aidbox(app)


async def on_startup(app):
    basic_auth = BasicAuth(
        login=app['settings'].APP_INIT_CLIENT_ID,
        password=app['settings'].APP_INIT_CLIENT_SECRET)
    app['init_http_client'] = ClientSession(auth=basic_auth)

    asyncio.get_event_loop().create_task(wait_and_init_aidbox(app))


async def on_cleanup(app):
    await app['init_http_client'].close()
    await app['sdk'].deinitialize()


async def on_shutdown(app):
    if not app['init_http_client'].closed:
        await app['init_http_client'].close()


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

