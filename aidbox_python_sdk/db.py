import json
import logging

from aiohttp import BasicAuth, ClientSession
from sqlalchemy import (
    BigInteger,
    Column,
    DateTime,
    Enum,
    MetaData,
    Table,
    Text,
    TypeDecorator,
    text,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.dialects.postgresql import dialect as postgresql_dialect
from sqlalchemy.sql.elements import ClauseElement

from aidbox_python_sdk.settings import Settings

from .exceptions import AidboxDBException

logger = logging.getLogger("aidbox_sdk.db")
table_metadata = MetaData()


class AidboxPostgresqlDialect(postgresql_dialect):
    # We don't need escaping at this level
    # All escaping will be done on the aidbox side
    _backslash_escapes = False


class _JSONB(TypeDecorator):
    impl = JSONB

    def process_literal_param(self, value, dialect):
        if isinstance(value, dict):
            return "'{}'".format(json.dumps(value).replace("'", "''"))
        if isinstance(value, str):
            return value
        raise ValueError(f"Don't know how to literal-quote value of type {type(value)}")


class _ARRAY(TypeDecorator):
    impl = ARRAY

    def process_literal_param(self, value, dialect):
        if isinstance(value, list):
            return f"ARRAY{value}"
        if isinstance(value, str):
            return value
        raise ValueError(f"Don't know how to literal-quote value of type {type(value)}")


def create_table(table_name):
    return Table(
        table_name,
        table_metadata,
        Column("id", Text, primary_key=True),
        Column("txid", BigInteger, nullable=False),
        Column("ts", DateTime(True), server_default=text("CURRENT_TIMESTAMP")),
        Column("cts", DateTime(True), server_default=text("CURRENT_TIMESTAMP")),
        Column("resource_type", Text, server_default=text("'App'::text")),
        Column(
            "status",
            Enum("created", "updated", "deleted", "recreated", name="resource_status"),
            nullable=False,
        ),
        Column("resource", _JSONB(astext_type=Text()), nullable=False, index=True),
        extend_existing=True,
    )


class DBProxy:
    _client = None
    _settings = None
    _table_cache = None

    def __init__(self, settings: Settings):
        self._settings = settings
        self._table_cache = {}

    async def initialize(self):
        basic_auth = BasicAuth(
            login=self._settings.APP_INIT_CLIENT_ID,
            password=self._settings.APP_INIT_CLIENT_SECRET,
        )
        self._client = ClientSession(auth=basic_auth)
        # TODO: remove _init_table_cache
        await self._init_table_cache()

    async def deinitialize(self):
        await self._client.close()

    async def raw_sql(self, sql_query, *, execute=False):
        """
        Executes SQL query and returns result. Specify `execute` to True
        if you want to execute `sql_query` that doesn't return result
        (for example, UPDATE without returning or CREATE INDEX and etc.)
        otherwise you'll get an AidboxDBException
        """
        if not self._client:
            raise ValueError("Client not set")
        if not isinstance(sql_query, str):
            raise ValueError("sql_query must be a str")
        if not execute and sql_query.count(";") > 1:
            logger.warning("Check that your query does not contain two queries separated by `;`")
        query_url = f"{self._settings.APP_INIT_URL}/$psql"
        async with self._client.post(
            query_url,
            json={"query": sql_query},
            params={"execute": "true"} if execute else {},
            raise_for_status=True,
        ) as resp:
            logger.debug("$psql answer %s", await resp.text())
            results = await resp.json()

            if results[0]["status"] == "error":
                raise AidboxDBException(results[0])
            return results[0].get("result", None)

    def compile_statement(self, statement):
        return str(
            statement.compile(
                dialect=AidboxPostgresqlDialect(),
                compile_kwargs={"literal_binds": True},
            )
        )

    async def alchemy(self, statement, *, execute=False):
        if not isinstance(statement, ClauseElement):
            raise ValueError("statement must be a sqlalchemy expression")
        query = self.compile_statement(statement)
        logger.debug("Built query:\n%s", query)
        return await self.raw_sql(query, execute=execute)

    async def _get_all_entities_name(self):
        # TODO: refactor using sdk.client and fetch_all
        query_url = f"{self._settings.APP_INIT_URL}/Entity?type=resource&_elements=id&_count=999"
        async with self._client.get(query_url, raise_for_status=True) as resp:
            json_resp = await resp.json()
            return [entry["resource"]["id"] for entry in json_resp["entry"]]

    async def _init_table_cache(self):
        table_names = await self._get_all_entities_name()
        self._table_cache = {
            **{table_name: {"table_name": table_name.lower()} for table_name in table_names},
            **{
                f"{table_name}History": {"table_name": f"{table_name.lower()}_history"}
                for table_name in table_names
            },
        }

    def __getattr__(self, item):
        if item in self._table_cache:
            cache = self._table_cache[item]
            if cache.get("table") is None:
                cache["table"] = create_table(cache["table_name"])
            return cache["table"]

        raise AttributeError


def row_to_resource(row):
    """
    Transforms raw row from resource's table to resource representation
    >>> import pprint
    >>> pprint.pprint(row_to_resource({
    ...     'resource': {'name': []},
    ...     'ts': 'ts',
    ...     'txid': 'txid',
    ...     'resource_type': 'Patient',
    ...     'meta': {'tag': 'created'},
    ...     'id': 'id',
    ... }))
    {'id': 'id',
     'meta': {'lastUpdated': 'ts', 'versionId': 'txid'},
     'name': [],
     'resourceType': 'Patient'}
    """
    resource = row["resource"]
    meta = row["resource"].get("meta", {})
    meta.update(
        {
            "lastUpdated": row["ts"],
            "versionId": str(row["txid"]),
        }
    )
    resource.update(
        {
            "resourceType": row["resource_type"],
            "id": row["id"],
            "meta": meta,
        }
    )
    return resource
