--
-- This is postgresql schema creation statements.
-- Add dictionary tables sql and validict schema & tables sql to make a complete postgres ddl script.
--

drop schema if exists dict cascade;
create schema dict;
grant usage on schema dict to public;
grant select on all tables in schema dict to public;
alter default privileges in schema dict grant select on tables to public;

set search_path = dict, pg_catalog;
