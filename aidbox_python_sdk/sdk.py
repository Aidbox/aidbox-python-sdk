import asyncio
import logging

import jsonschema
from fhirpy.base.exceptions import OperationOutcome

from .aidboxpy import AsyncAidboxClient
from .db_migrations import sdk_migrations

logger = logging.getLogger("aidbox_sdk")


class SDK:
    def __init__(  # noqa: PLR0913
        self,
        settings,
        *,
        entities=None,
        resources=None,
        seeds=None,
        migrations=None,
    ):
        self.settings = settings
        self._subscriptions = {}
        self._subscription_handlers = {}
        self._operations = {}
        self._operation_handlers = {}
        self._manifest = {
            "apiVersion": 1,
            "type": "app",
            "id": settings.APP_ID,
            "endpoint": {
                "url": f"{settings.APP_URL}/aidbox",
                "type": "http-rpc",
                "secret": settings.APP_SECRET,
            },
        }
        self._resources = resources or {}
        self._entities = entities or {}
        self._seeds = seeds or {}
        self._migrations = migrations or []
        self._app_endpoint_name = f"{settings.APP_ID}-endpoint"
        self._sub_triggered = {}
        self._test_start_txid = None

    async def apply_migrations(self, client: AsyncAidboxClient):
        await client.resource(
            "Bundle",
            type="transaction",
            entry=[
                {
                    "resource": self._migrations + sdk_migrations,
                    "request": {"method": "POST", "url": "/db/migrations"},
                }
            ],
        ).save()

    async def create_seed_resources(self, client: AsyncAidboxClient):
        entries = []
        for entity, resources in self._seeds.items():
            for resource_id, resource in resources.items():
                if resource.get("id") and resource["id"] != resource_id:
                    logger.warning(
                        "Resource '%s' key id=%s is not equal to the resource 'id'=%s ",
                        entity,
                        resource_id,
                        resource["id"],
                    )
                entry = {"resource": {**resource, "id": resource_id, "resourceType": entity}}
                # Conditional create
                entry["request"] = {
                    "method": "POST",
                    "url": f"/{entity}?_id={resource_id}",
                }
                entries.append(entry)
        bundle = client.resource("Bundle", type="transaction", entry=entries)
        await bundle.save()

    def build_manifest(self):
        if self._resources:
            self._manifest["resources"] = self._resources
        if self._entities:
            self._manifest["entities"] = self._entities
        if self._subscriptions:
            self._manifest["subscriptions"] = self._subscriptions
        if self._operations:
            self._manifest["operations"] = self._operations
        return self._manifest

    def subscription(self, entity):
        def wrap(func):
            path = func.__name__
            self._subscriptions[entity] = {"handler": path}

            async def handler(event, request):
                if self._test_start_txid is not None:
                    # Skip outside test
                    if self._test_start_txid == -1:
                        return None

                    # Skip inside another test
                    if int(event["tx"]["id"]) < self._test_start_txid:
                        return None
                coro_or_result = func(event, request)
                if asyncio.iscoroutine(coro_or_result):
                    result = await coro_or_result
                else:
                    logger.warning("Synchronous subscription handler is deprecated: %s", path)
                    result = coro_or_result

                if entity in self._sub_triggered:
                    future, counter = self._sub_triggered[entity]
                    if counter > 1:
                        self._sub_triggered[entity] = (future, counter - 1)
                    elif future.done():
                        pass
                        # logger.warning('Uncaught subscription for %s', entity)
                    else:
                        future.set_result(True)

                return result

            self._subscription_handlers[path] = handler
            return func

        return wrap

    def get_subscription_handler(self, path):
        return self._subscription_handlers.get(path)

    def was_subscription_triggered_n_times(self, entity, counter):
        timeout = 10

        future = asyncio.Future()
        self._sub_triggered[entity] = (future, counter)
        asyncio.get_event_loop().call_later(
            timeout,
            lambda: None if future.done() else future.set_exception(Exception()),
        )

        return future

    def was_subscription_triggered(self, entity):
        return self.was_subscription_triggered_n_times(entity, 1)

    def operation(  # noqa: PLR0913
        self,
        methods,
        path,
        public=False,
        access_policy=None,
        request_schema=None,
        timeout=None,
    ):
        if public and access_policy is not None:
            raise ValueError("Operation might be public or have access policy, not both")

        request_validator = None
        if request_schema:
            request_validator = jsonschema.Draft202012Validator(schema=request_schema)

        def wrap(func):
            if not isinstance(path, list):
                raise ValueError("`path` must be a list")
            if not isinstance(methods, list):
                raise ValueError("`methods` must be a list")
            _str_path = []
            for p in path:
                if isinstance(p, str):
                    _str_path.append(p)
                elif isinstance(p, dict):
                    _str_path.append("__{}__".format(p["name"]))

            def wrapped_func(operation, request):
                if request_validator:
                    validate_request(request_validator, request)
                return func(operation, request)

            for method in methods:
                operation_id = "{}.{}.{}.{}".format(
                    method, func.__module__, func.__name__, "_".join(_str_path)
                ).replace("$", "d")
                self._operations[operation_id] = {
                    "method": method,
                    "path": path,
                    **({"timeout": timeout} if timeout else {}),
                }
                self._operation_handlers[operation_id] = wrapped_func
                if public is True:
                    self._set_access_policy_for_public_op(operation_id)
                elif access_policy is not None:
                    self._set_operation_access_policy(operation_id, access_policy)
            return func

        return wrap

    def get_operation_handler(self, operation_id):
        return self._operation_handlers.get(operation_id)

    def _set_operation_access_policy(self, operation_id, access_policy):
        if "AccessPolicy" not in self._resources:
            self._resources["AccessPolicy"] = {}
        self._resources["AccessPolicy"][operation_id] = {
            "link": [{"id": operation_id, "resourceType": "Operation"}],
            "engine": access_policy["engine"],
            "schema": access_policy["schema"],
        }

    def _set_access_policy_for_public_op(self, operation_id):
        if "AccessPolicy" not in self._resources:
            self._resources["AccessPolicy"] = {}
        if self._app_endpoint_name not in self._resources["AccessPolicy"]:
            self._resources["AccessPolicy"][self._app_endpoint_name] = {
                "link": [],
                "engine": "allow",
            }
        self._resources["AccessPolicy"][self._app_endpoint_name]["link"].append(
            {
                "id": operation_id,
                "resourceType": "Operation",
            }
        )


def validate_request(request_validator, request):
    errors = list(request_validator.iter_errors(request))

    if errors:
        raise OperationOutcome(
            resource={
                "resourceType": "OperationOutcome",
                "text": {"status": "generated", "div": "Invalid request"},
                "issue": [
                    {
                        "severity": "fatal",
                        "code": "invalid",
                        "expression": [".".join([str(x) for x in ve.absolute_path])],
                        "diagnostics": ve.message,
                    }
                    for ve in errors
                ],
            }
        )
