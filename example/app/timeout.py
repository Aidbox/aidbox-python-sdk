import asyncio
from aiohttp import web

from app.sdk import sdk


@sdk.operation(["GET"], ["$default-timeout"])
async def operation_handler_with_default_timeout(operation, request):
    await asyncio.sleep(1)
    return web.json_response({"result": "success"})


@sdk.operation(["GET"], ["$sleep", {"name": "sleep-ms"}], timeout=2000)
async def operation_handler_with_custom_timeout(operation, request):
    sleep_duration = int(request["route-params"]["sleep-ms"])
    await asyncio.sleep(sleep_duration)
    return web.json_response({"result": "success"})
