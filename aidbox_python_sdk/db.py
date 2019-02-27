import logging
import json
from sqlalchemy import BigInteger, Column, DateTime, Enum, Text, text, TypeDecorator
from sqlalchemy.dialects.postgresql import JSONB, dialect as postgresql_dialect
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()
metadata = Base.metadata
logger = logging.getLogger()


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

    async def make_query(self, sql_query):
        if not self._client:
            raise ValueError('Client not set')
        async with self._client.post(
                '{}/$psql'.format(self._devbox_url), json={'query': sql_query}) as resp:
            # logger.debug(await resp.text())
            if 200 <= resp.status < 300:
                return await resp.json()
            raise ValueError('SQL response error: {}, status: {}'.format(await resp.text(), resp.status))

    async def compile_statement(self, statement):
        # logger.debug('Type of the statement: {}'.format(type(statement)))
        return str(statement.compile(dialect=postgresql_dialect(), compile_kwargs={"literal_binds": True}))

    async def _get_all_table_names(self):
        query = """
            SELECT tablename FROM pg_catalog.pg_tables
            WHERE
            schemaname != 'pg_catalog'
            AND schemaname != 'information_schema'
            AND tablename NOt in ('_box', 'devboxtoken')
            AND tablename not like '%_history';
        """
        tables = await self.make_query(query)
        return tables

    def _create_table_mapping(self, table_name):
        mapping = type(table_name.capitalize(), (BaseAidboxMapping,), {'__tablename__': table_name})
        return mapping()

    async def create_all_mappings(self):
        result = await self._get_all_table_names()
        tables = result[0]['result']
        for t in tables:
            setattr(self, t['tablename'].capitalize(), self._create_table_mapping(t['tablename']))
        logger.debug('{} table mappings were created'.format(len(tables)))
