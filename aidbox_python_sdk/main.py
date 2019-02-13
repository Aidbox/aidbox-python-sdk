from os import getenv
from pathlib import Path
from aiohttp import web, ClientSession, BasicAuth
from .settings import Settings
from .views import index, init_aidbox

THIS_DIR = Path(__file__).parent
BASE_DIR = THIS_DIR.parent


def setup_routes(app):
    app.router.add_get('/', index, name='index')
    app.router.add_get('/{tail:.*}', index)
    app.router.add_post('/{tail:.*}', index)


async def on_startup(app):
    basic_auth = BasicAuth(
        login=getenv('APP_INIT_CLIENT_ID'),
        password=getenv('APP_INIT_CLIENT_SECRET'))
    app['client'] = ClientSession(auth=basic_auth)
    await init_aidbox(app)


async def on_cleanup(app):
    await app['client'].close()


async def create_app():
    app = web.Application(debug=True)

    app.on_startup.append(on_startup)
    app.on_cleanup.append(on_cleanup)

    settings = Settings()
    app.update(
        name='aidbox-python-sdk',
        settings=settings
    )
    setup_routes(app)
    return app
