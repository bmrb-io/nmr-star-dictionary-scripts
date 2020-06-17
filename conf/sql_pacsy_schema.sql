-- ****************************************************************************************
--
--

drop schema if exists pacsy cascade;
create schema pacsy;
grant usage on schema pacsy to public;
grant select on all tables in schema pacsy to public;
alter default privileges in schema pacsy grant select on tables to public;

set search_path = pacsy, pg_catalog;

--
-- Name: software; Type: TABLE; Schema: pacsy; Owner: -; Tablespace:
--

CREATE TABLE software (
    "Sf_category" text,
    "Sf_framecode" text,
    "Entry_ID" text,
    "Sf_ID" integer,
    "ID" text,
    "Name" text,
    "Version" text,
    "Details" text
);

--
-- Name: struct_anno_char; Type: TABLE; Schema: pacsy; Owner: -; Tablespace:
--

CREATE TABLE struct_anno_char (
    "ID" text,
    "Atom_site_model_ID" text,
    "Assembly_ID" text,
    "Entity_assembly_ID" text,
    "Entity_ID" text,
    "Comp_index_ID" text,
    "Comp_ID" text,
    "PDB_strand_ID" text,
    "Secondary_structure_code" text,
    "Edge_designation" text,
    "Phi_angle" text,
    "Psi_angle" text,
    "Hydrophobicity" text,
    "Solvent_accessible_surface_area" text,
    "Sf_ID" integer,
    "Entry_ID" text,
    "Structure_annotation_ID" text
);

--
-- Name: struct_anno_software; Type: TABLE; Schema: pacsy; Owner: -; Tablespace:
--
CREATE TABLE struct_anno_software (
    "Software_ID" text,
    "Software_label" text,
    "Method_ID" text,
    "Method_label" text,
    "Sf_ID" integer,
    "Entry_ID" text,
    "Structure_annotation_ID" text
);

--
-- Name: struct_classification; Type: TABLE; Schema: pacsy; Owner: -; Tablespace:
--

CREATE TABLE struct_classification (
    "ID" text,
    "Code" text,
    "Class" text,
    "Fold" text,
    "Superfamily" text,
    "Family" text,
    "DB_source_ID" text,
    "Description" text,
    "Sf_ID" integer,
    "Entry_ID" text,
    "Structure_annotation_ID" text
);

--
-- Name: structure_annotation; Type: TABLE; Schema: pacsy; Owner: -; Tablespace:
--

CREATE TABLE structure_annotation (
    "Sf_category" text,
    "Sf_framecode" text,
    "Entry_ID" text,
    "Sf_ID" integer,
    "ID" text,
    "PDB_ID" text,
    "DB_queried_date" text,
    "DB_source" text,
    "DB_electronic_address" text,
    "DB_source_release_designation" text,
    "DB_source_release_date" text,
    "Details" text
);

--
-- Name: task; Type: TABLE; Schema: pacsy; Owner: -; Tablespace:
--

CREATE TABLE task (
    "Task" text,
    "Sf_ID" integer,
    "Entry_ID" text,
    "Software_ID" text
);

--
-- Name: vendor; Type: TABLE; Schema: pacsy; Owner: -; Tablespace:
--

CREATE TABLE vendor (
    "Name" text,
    "Address" text,
    "Electronic_address" text,
    "Sf_ID" integer,
    "Entry_ID" text,
    "Software_ID" text
);
