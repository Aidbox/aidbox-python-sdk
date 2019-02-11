from aiohttp import web


async def index(request):
    """
    This is the view handler for the "/" url.

    :param request: the request object see http://aiohttp.readthedocs.io/en/stable/web_reference.html#request
    :return: aiohttp.web.Response object
    """

    return web.json_response({'hello': 'world'})
