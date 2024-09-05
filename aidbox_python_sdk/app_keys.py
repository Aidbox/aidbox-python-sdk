from aiohttp import web

from aidbox_python_sdk.aidboxpy import AsyncAidboxClient
from aidbox_python_sdk.db import DBProxy
from aidbox_python_sdk.sdk import SDK
from aidbox_python_sdk.settings import Settings

db: web.AppKey[DBProxy] = web.AppKey("db", DBProxy)
client: web.AppKey[AsyncAidboxClient] = web.AppKey("client", AsyncAidboxClient)
sdk: web.AppKey[SDK] = web.AppKey("sdk", SDK)
settings: web.AppKey[Settings] = web.AppKey("settings", Settings)
