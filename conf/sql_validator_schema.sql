-- ****************************************************************************************
--
-- some day I'll clean this mess up...
--
-- validation dictionary
--

drop schema if exists validict cascade;
create schema validict;
grant usage on schema validict to public;
grant select on all tables in schema validict to public;
alter default privileges in schema validict grant select on tables to public;

set search_path = validict, pg_catalog;

