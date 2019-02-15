import asyncio
import logging
from pathlib import Path
from aiohttp import web, ClientSession, BasicAuth
from .handlers import routes

logger = logging.getLogger()
THIS_DIR = Path(__file__).parent
BASE_DIR = THIS_DIR.parent


def setup_routes(app):
    app.add_routes(routes)


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


async def on_startup(app):
    basic_auth = BasicAuth(
        login=app['settings'].APP_INIT_CLIENT_ID,
        password=app['settings'].APP_INIT_CLIENT_SECRET)
    app['client'] = ClientSession(auth=basic_auth)


async def on_cleanup(app):
    await app['client'].close()


async def create_app(settings, manifest, debug=False):
    app = web.Application(debug=debug)
    app.on_startup.append(on_startup)
    app.on_cleanup.append(on_cleanup)
    app.update(
        name='aidbox-python-sdk',
        settings=settings,
        manifest=manifest,
        init_aidbox_app=init_aidbox
    )
    setup_routes(app)
    return app


async def start_site(runner):
    print("======== Running on {} ========\n"
          "(Press CTRL+C to quit)".format(runner.app['settings'].APP_PORT))
    site = web.TCPSite(runner, 'localhost', runner.app['settings'].APP_PORT)
    await site.start()
    await init_aidbox(runner.app)


def run_standalone_app(settings, manifest, debug=False):
    loop = asyncio.get_event_loop()
    app = create_app(settings, manifest, debug=debug)
    if asyncio.iscoroutine(app):
        app = loop.run_until_complete(app)
    runner = web.AppRunner(app)
    loop.run_until_complete(runner.setup())

    try:
        loop.run_until_complete(start_site(runner))
        try:
            loop.run_forever()
        except (web.GracefulExit, KeyboardInterrupt):
            pass
    finally:
        loop.run_until_complete(runner.cleanup())
    loop.close()
    # web.run_app(app, port=settings.APP_PORT)
