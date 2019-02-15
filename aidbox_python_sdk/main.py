from pathlib import Path
from aiohttp import web, ClientSession, BasicAuth
from .handlers import routes

THIS_DIR = Path(__file__).parent
BASE_DIR = THIS_DIR.parent


def setup_routes(app):
    app.add_routes(routes)


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
        manifest=manifest
    )
    setup_routes(app)
    return app


def run_standalone_app(settings, manifest, debug=False):
    app = create_app(settings, manifest, debug=debug)
    web.run_app(app, port=settings.APP_PORT)