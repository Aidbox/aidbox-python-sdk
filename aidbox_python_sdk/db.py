import logging
import json
from sqlalchemy import BigInteger, Column, DateTime, Enum, Text, text, TypeDecorator
from sqlalchemy.sql.elements import ClauseElement
from sqlalchemy.dialects.postgresql import JSONB, dialect as postgresql_dialect
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()
metadata = Base.metadata
logger = logging.getLogger('aidbox_sdk.db')


class _JSONB(TypeDecorator):
    impl = JSONB

    def process_literal_param(self, value, dialect):
        if isinstance(value, dict):
            return '\'{}\''.format(json.dumps(value))
        elif isinstance(value, str):
            return value
        raise ValueError('Don\'t know how to literal-quote value of type {}'.format(type(value)))


class BaseAidboxMapping(Base):
    __abstract__ = True

    id = Column(Text, primary_key=True)
    txid = Column(BigInteger, nullable=False)
    ts = Column(DateTime(True), server_default=text("CURRENT_TIMESTAMP"))
    resource_type = Column(Text, server_default=text("'App'::text"))
    status = Column(Enum('created', 'updated', 'deleted', 'recreated', name='resource_status'), nullable=False)
    resource = Column(_JSONB(astext_type=Text()), nullable=False, index=True)


class DBProxy(object):
    _client = None
    _devbox_url = None

    def __init__(self, settings):
        self._devbox_url = settings.APP_INIT_URL

    def set_client(self, client):
        self._client = client

    async def raw_sql(self, sql_query, execute=False):
        if not self._client:
            raise ValueError('Client not set')
        if not isinstance(sql_query, str):
            ValueError('sql_query must be a str')
        query_url = '{}/$psql'.format(self._devbox_url)
        async with self._client.post(
                query_url,
                json={'query': sql_query},
                params={'execute': 'true'} if execute else {},
                raise_for_status=True
        ) as resp:
            logger.debug('$psql answer {0}'.format(await resp.text()))
            return await resp.json()

    async def compile_statement(self, statement):
        return str(statement.compile(dialect=postgresql_dialect(), compile_kwargs={"literal_binds": True}))

    async def alchemy(self, statement):
        if not isinstance(statement, ClauseElement):
            ValueError('statement must be a sqlalchemy expression')
        query = await self.compile_statement(statement)
        logger.debug('Built query:\n%s', query)
        return await self.raw_sql(query)

    async def _get_all_entities_name(self):
        query_url = '{}/Entity?type=resource&_elements=id'.format(self._devbox_url)
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
        logger.debug('{} table mappings were created'.format(len(tables)))
