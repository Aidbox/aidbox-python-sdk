sdk_migrations = [
    {
        "id": "20190909_add_drop_before",
        "sql": """
DROP FUNCTION IF EXISTS drop_before_all(integer);

CREATE FUNCTION drop_before_all(integer) RETURNS VOID AS $$
declare
e record;
BEGIN
FOR e IN (select LOWER(entity.id) as t_name from entity where resource#>>'{type}' = 'resource' and id != 'OperationOutcome') LOOP
    EXECUTE 'delete from "' || e.t_name || '" where txid > ' || $1 ;
END LOOP;
END;

$$ LANGUAGE plpgsql;""",
    },
    {
        "id": "20240913_change_drop_before_all",
        "sql": """
DROP FUNCTION IF EXISTS drop_before_all(integer);

CREATE FUNCTION drop_before_all(integer) RETURNS VOID AS $$
declare
e record;
BEGIN
FOR e IN (
  SELECT table_name
  FROM information_schema.columns
  WHERE column_name = 'txid' AND table_schema = 'public' AND table_name NOT LIKE '%_history'
) LOOP
    EXECUTE 'DELETE FROM "' || e.table_name || '" WHERE txid > ' || $1 ;
END LOOP;
END;

$$ LANGUAGE plpgsql;""",
    },
]
