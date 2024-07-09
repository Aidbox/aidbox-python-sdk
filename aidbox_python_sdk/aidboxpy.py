# type: ignore because fhir-py is not typed properly
from abc import ABC

from fhirpy.base import (
    AsyncClient,
    AsyncReference,
    AsyncResource,
    AsyncSearchSet,
    SyncClient,
    SyncReference,
    SyncResource,
    SyncSearchSet,
)
from fhirpy.base.resource import BaseReference, BaseResource
from fhirpy.base.searchset import AbstractSearchSet

__title__ = "aidbox-py"
__version__ = "1.3.0"
__author__ = "beda.software"
__license__ = "None"
__copyright__ = "Copyright 2021 beda.software"

# Version synonym
VERSION = __version__


class AidboxSearchSet(AbstractSearchSet, ABC):
    def assoc(self, element_path):
        return self.clone(**{"_assoc": element_path})


class SyncAidboxSearchSet(SyncSearchSet, AidboxSearchSet):
    pass


class AsyncAidboxSearchSet(AsyncSearchSet, AidboxSearchSet):
    pass


class BaseAidboxResource(BaseResource, ABC):
    def is_reference(self, value):
        if not isinstance(value, dict):
            return False

        return (
            "resourceType" in value
            and ("id" in value or "url" in value)
            and not (
                set(value.keys())
                - {
                    "resourceType",
                    "id",
                    "_id",
                    "resource",
                    "display",
                    "uri",
                    "localRef",
                    "identifier",
                    "extension",
                }
            )
        )


class SyncAidboxResource(BaseAidboxResource, SyncResource):
    pass


class AsyncAidboxResource(BaseAidboxResource, AsyncResource):
    pass


class BaseAidboxReference(BaseReference, ABC):
    @property
    def reference(self):
        """
        Returns reference if local resource is saved
        """
        if self.is_local:
            return f"{self.resource_type}/{self.id}"
        return self.get("url", None)

    @property
    def id(self):
        if self.is_local:
            return self.get("id", None)
        return None

    @property
    def resource_type(self):
        """
        Returns resource type if reference specifies to the local resource
        """
        if self.is_local:
            return self.get("resourceType", None)
        return None

    @property
    def is_local(self):
        return not self.get("url")


class SyncAidboxReference(BaseAidboxReference, SyncReference):
    pass


class AsyncAidboxReference(BaseAidboxReference, AsyncReference):
    pass


class SyncAidboxClient(SyncClient):
    searchset_class = SyncAidboxSearchSet
    resource_class = SyncAidboxResource

    def reference(self, resource_type=None, id=None, reference=None, **kwargs):  # noqa: A002
        resource_type = kwargs.pop("resourceType", resource_type)
        if reference:
            if reference.count("/") > 1:
                return SyncAidboxReference(self, url=reference, **kwargs)
            resource_type, id = reference.split("/")  # noqa: A001
        if not resource_type and not id:
            raise TypeError("Arguments `resource_type` and `id` or `reference`are required")
        return SyncAidboxReference(self, resourceType=resource_type, id=id, **kwargs)


class AsyncAidboxClient(AsyncClient):
    searchset_class = AsyncAidboxSearchSet
    resource_class = AsyncAidboxResource

    def reference(self, resource_type=None, id=None, reference=None, **kwargs):  # noqa: A002
        resource_type = kwargs.pop("resourceType", resource_type)
        if reference:
            if reference.count("/") > 1:
                return AsyncAidboxReference(self, url=reference, **kwargs)
            resource_type, id = reference.split("/")  # noqa: A001
        if not resource_type and not id:
            raise TypeError("Arguments `resource_type` and `id` or `reference`are required")
        return AsyncAidboxReference(self, resourceType=resource_type, id=id, **kwargs)
