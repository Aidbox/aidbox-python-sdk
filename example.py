import logging
import coloredlogs
from aiohttp import web

from aidbox_python_sdk.main import run_standalone_app
from aidbox_python_sdk.settings import Settings
from aidbox_python_sdk.manifest import Manifest

coloredlogs.install(level='DEBUG', fmt='%(asctime)s %(levelname)s %(message)s')

settings = Settings(**{})
manifest = Manifest(settings)


def main():
    logging.info('Started')
    run_standalone_app(settings, manifest, debug=True)


@manifest.subscription('User')
async def user_sub(event):
    logging.debug('User subscription handler')
    logging.debug('Event: {}'.format(event))
    return web.json_response({})


@manifest.subscription('Patient')
def patient_sub(event):
    logging.debug('Patient subscription handler')
    logging.debug('Event: {}'.format(event))
    return web.json_response({})


if __name__ == '__main__':
    main()
