import asyncio
from aiohttp import web

from app.sdk import sdk


@sdk.operation(["GET"], ["$default-timeout"])
async def operation_handler_with_default_timeout(operation, request):
    await asyncio.sleep(1)
    return web.json_response({"result": "success"})


@sdk.operation(["GET"], ["$custom-timeout"], timeout=500)
async def operation_handler_with_custom_timeout(operation, request):
    await asyncio.sleep(1)
    return web.json_response({"result": "should_not_be_returned"})
