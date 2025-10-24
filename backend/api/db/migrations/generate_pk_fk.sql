-- Generate DDL statements for all Primary Keys and Foreign Keys across all non-system schemas
-- Usage (psql):
--   \o pk_fk_ddl.sql
--   \i backend/api/db/migrations/2025-10-22_generate_pk_fk.sql
--   \o

SET search_path = public;

-- ==========================
-- Primary Key constraints
-- ==========================
WITH pk AS (
  SELECT
    con.oid               AS con_oid,
    con.conname           AS constraint_name,
    n.nspname             AS schema_name,
    c.relname             AS table_name,
    array_agg(a.attname ORDER BY k.ord) AS cols
  FROM pg_constraint con
  JOIN pg_class      c  ON c.oid = con.conrelid
  JOIN pg_namespace  n  ON n.oid = c.relnamespace
  JOIN LATERAL unnest(con.conkey) WITH ORDINALITY AS k(attnum, ord) ON TRUE
  JOIN pg_attribute  a  ON a.attrelid = c.oid AND a.attnum = k.attnum
  WHERE con.contype = 'p'
    AND n.nspname NOT IN ('pg_catalog', 'information_schema')
  GROUP BY con.oid, con.conname, n.nspname, c.relname
)
SELECT
  'ALTER TABLE ONLY '
  || quote_ident(schema_name) || '.' || quote_ident(table_name)
  || ' ADD CONSTRAINT ' || quote_ident(constraint_name)
  || ' PRIMARY KEY ('
  || array_to_string(ARRAY(SELECT quote_ident(x) FROM unnest(cols) x), ', ')
  || ');' AS ddl
FROM pk
ORDER BY schema_name, table_name, constraint_name;


-- ==========================
-- Foreign Key constraints
-- ==========================
WITH fk AS (
  SELECT
    con.oid               AS con_oid,
    con.conname           AS constraint_name,
    n.nspname             AS schema_name,
    c.relname             AS table_name,
    fn.nspname            AS ref_schema_name,
    fc.relname            AS ref_table_name,
    con.confupdtype,
    con.confdeltype,
    con.condeferrable,
    con.condeferred,
    array_agg(la.attname ORDER BY k.ord)  AS cols,
    array_agg(ra.attname ORDER BY k.ord)  AS ref_cols
  FROM pg_constraint con
  JOIN pg_class      c  ON c.oid = con.conrelid
  JOIN pg_namespace  n  ON n.oid = c.relnamespace
  JOIN pg_class      fc ON fc.oid = con.confrelid
  JOIN pg_namespace  fn ON fn.oid = fc.relnamespace
  JOIN LATERAL unnest(con.conkey)  WITH ORDINALITY AS k (attnum, ord)  ON TRUE
  JOIN pg_attribute  la ON la.attrelid = c.oid  AND la.attnum = k.attnum
  JOIN LATERAL unnest(con.confkey) WITH ORDINALITY AS rk(attnum, ord) ON rk.ord = k.ord
  JOIN pg_attribute  ra ON ra.attrelid = fc.oid AND ra.attnum = rk.attnum
  WHERE con.contype = 'f'
    AND n.nspname NOT IN ('pg_catalog', 'information_schema')
  GROUP BY con.oid, con.conname, n.nspname, c.relname,
           fn.nspname, fc.relname,
           con.confupdtype, con.confdeltype, con.condeferrable, con.condeferred
)
SELECT
  'ALTER TABLE ONLY '
  || quote_ident(schema_name) || '.' || quote_ident(table_name)
  || ' ADD CONSTRAINT ' || quote_ident(constraint_name)
  || ' FOREIGN KEY ('
  || array_to_string(ARRAY(SELECT quote_ident(x) FROM unnest(cols) x), ', ')
  || ') REFERENCES '
  || quote_ident(ref_schema_name) || '.' || quote_ident(ref_table_name)
  || ' ('
  || array_to_string(ARRAY(SELECT quote_ident(x) FROM unnest(ref_cols) x), ', ')
  || ')'
  || CASE confupdtype
       WHEN 'c' THEN ' ON UPDATE CASCADE'
       WHEN 'n' THEN ' ON UPDATE SET NULL'
       WHEN 'd' THEN ' ON UPDATE SET DEFAULT'
       WHEN 'r' THEN ' ON UPDATE RESTRICT'
       ELSE ''  -- 'a' => NO ACTION
     END
  || CASE confdeltype
       WHEN 'c' THEN ' ON DELETE CASCADE'
       WHEN 'n' THEN ' ON DELETE SET NULL'
       WHEN 'd' THEN ' ON DELETE SET DEFAULT'
       WHEN 'r' THEN ' ON DELETE RESTRICT'
       ELSE ''  -- 'a' => NO ACTION
     END
  || CASE WHEN condeferrable
          THEN (CASE WHEN condeferred THEN ' DEFERRABLE INITIALLY DEFERRED'
                     ELSE ' DEFERRABLE INITIALLY IMMEDIATE' END)
          ELSE ' NOT DEFERRABLE' END
  || ';' AS ddl
FROM fk
ORDER BY schema_name, table_name, constraint_name;

