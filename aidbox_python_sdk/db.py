import logging
import json

from aiohttp import BasicAuth, ClientSession
from sqlalchemy import (BigInteger, Column, DateTime, Enum,
    Text, text, TypeDecorator)
from sqlalchemy.sql.elements import ClauseElement
from sqlalchemy.dialects.postgresql import JSONB, ARRAY, dialect as postgresql_dialect
from sqlalchemy.ext.declarative import declarative_base

from .exceptions import AidboxDBException


Base = declarative_base()
metadata = Base.metadata
logger = logging.getLogger('aidbox_sdk.db')


class _JSONB(TypeDecorator):
    impl = JSONB

    def process_literal_param(self, value, dialect):
        if isinstance(value, dict):
            return '\'{}\''.format(json.dumps(value).replace("'", "''"))
        elif isinstance(value, str):
            return value
        raise ValueError(
            'Don\'t know how to literal-quote '
            'value of type {}'.format(type(value)))


class _ARRAY(TypeDecorator):
    impl = ARRAY

    def process_literal_param(self, value, dialect):
        if isinstance(value, list):
            return 'ARRAY{}'.format(value)
        elif isinstance(value, str):
            return value
        raise ValueError('Don\'t know how to literal-quote value of type {}'.format(type(value)))


class BaseAidboxMapping(Base):
    __abstract__ = True

    id = Column(Text, primary_key=True)
    txid = Column(BigInteger, nullable=False)
    ts = Column(DateTime(True), server_default=text("CURRENT_TIMESTAMP"))
    resource_type = Column(Text, server_default=text("'App'::text"))
    status = Column(Enum('created', 'updated', 'deleted', 'recreated',
                         name='resource_status'), nullable=False)
    resource = Column(_JSONB(astext_type=Text()), nullable=False, index=True)


class DBProxy(object):
    _client = None
    _devbox_url = None

    def __init__(self, settings):
        self._devbox_url = settings.APP_INIT_URL

    async def initialize(self, config):
        basic_auth = BasicAuth(
            login=config['client']['id'],
            password=config['client']['secret'])
        self._client = ClientSession(auth=basic_auth)
        await self.create_all_mappings()

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
            raise ValueError('Client not set')
        if not isinstance(sql_query, str):
            ValueError('sql_query must be a str')
        if not execute and sql_query.count(';') > 1:
            logger.warning(
                'Check that your query does not '
                'contain two queries separated by `;`')
        query_url = '{}/$psql'.format(self._devbox_url)
        async with self._client.post(
                query_url,
                json={'query': sql_query},
                params={'execute': 'true'} if execute else {},
                raise_for_status=True
        ) as resp:
            logger.debug('$psql answer {0}'.format(await resp.text()))
            results = await resp.json()

            if results[0]['status'] == 'error':
                raise AidboxDBException(results[0])
            return results[0].get('result', None)

    def compile_statement(self, statement):
        return str(statement.compile(
            dialect=postgresql_dialect(),
            compile_kwargs={"literal_binds": True}))

    async def alchemy(self, statement, *, execute=False):
        if not isinstance(statement, ClauseElement):
            ValueError('statement must be a sqlalchemy expression')
        query = self.compile_statement(statement)
        logger.debug('Built query:\n%s', query)
        return await self.raw_sql(query, execute=execute)

    async def _get_all_entities_name(self):
        query_url = '{}/Entity?type=resource&_elements=id&_count=10000'.format(
            self._devbox_url)
        async with self._client.get(query_url, raise_for_status=True) as resp:
            json_resp = await resp.json()
            return [entry['resource']['id'] for entry in json_resp['entry']]

    def _create_table_mapping(self, table_name):
        mapping = type(
            table_name.capitalize(),
            (BaseAidboxMapping,),
            {'__tablename__': table_name})
        return mapping()

    async def create_all_mappings(self):
        tables = await self._get_all_entities_name()

        for t in tables:
            setattr(self, t, self._create_table_mapping(t.lower()))

        for t in tables:
            setattr(self, '{}History'.format(t), self._create_table_mapping('{}_history'.format(t.lower())))

        logger.debug('{} table mappings were created'.format(len(tables)))


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
    resource = row['resource']
    meta = row['resource'].get('meta', {})
    meta.update({
        'lastUpdated': row['ts'],
        'versionId': str(row['txid']),
    })
    resource.update({
        'resourceType': row['resource_type'],
        'id': row['id'],
        'meta': meta,
    })
    return resource
