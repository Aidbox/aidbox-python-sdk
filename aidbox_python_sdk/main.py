from pathlib import Path

from aiohttp import web

from .settings import Settings
from .views import index


THIS_DIR = Path(__file__).parent
BASE_DIR = THIS_DIR.parent


def setup_routes(app):
    app.router.add_get('/', index, name='index')


async def create_app():
    app = web.Application()
    settings = Settings()
    app.update(
        name='aidbox-python-sdk',
        settings=settings
    )

    setup_routes(app)
    return app
