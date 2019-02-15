from aiohttp import web

from aidbox_python_sdk.main import run_standalone_app
from aidbox_python_sdk.handlers import routes
from aidbox_python_sdk.settings import Settings
from aidbox_python_sdk.manifest import Manifest


settings = Settings(**{})
manifest = Manifest(routes, settings)


def main():
    run_standalone_app(settings, manifest.build(), debug=True)


@manifest.subscription('/test', 'User')
async def init(request):
    return web.json_response({'msg': 'Hi there!'})


if __name__ == '__main__':
    main()