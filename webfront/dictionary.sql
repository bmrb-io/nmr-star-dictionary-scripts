--
-- this differs from the "main" script in use of schema only
-- well, and the main table name -- I might rename it in the main dictionary sometime
--
drop schema if exists dict cascade;
create schema dict;
set search_path = dict, pg_catalog;

CREATE TABLE val_item_tbl (
    dictionaryseq        integer      primary key,
    originalcategory     text NOT NULL,
    aditcatmanflg        char(2)      NOT NULL,
    aditcatviewtype      char(5)      NOT NULL,
    aditsupercatid       text NOT NULL,
    aditsupercatname     text NOT NULL,
    aditcatgrpid         text NOT NULL,
    aditcatviewname      text,
    aditinitialrows      integer      ,
    originaltag          text NOT NULL unique,
    aditexists           char(2)      ,
    aditviewflags        text NOT NULL,
    enumeratedflg        char(1)      ,
    itemenumclosedflg    char(2)      ,
    adititemviewname     text,
    aditformcode         integer      ,
    dbtype               text NOT NULL,
    bmrbtype             text,
    dbnullable           text,
    internalflag         char(1)      ,
    rowIndexFlg          char(1)      ,
    lclidflg             char(1)      ,
    lclsfidflg           char(1)      ,
    sfidflg              char(1)      ,
    sfNameFlg            char(1)      ,
    sfcategoryflg        char(1)      ,
    sfPointerFlg         char(1)      ,
    primarykey           char(1)      ,
    foreignkeygroup      text,
    foreigntable         text,
    foreigncolumn        text,
    refkeygroup          text,
    reftable             text,
    refcolumn            text,
    indexflag            char(1)      ,
    dbtablemanual        text NOT NULL,
    dbcolumnmanual       text NOT NULL,
    tagcategory          text NOT NULL,
    tagfield             text NOT NULL,
    loopflag             char(1)      ,
    seq                  integer      NOT NULL,
    dbflg                char(1)      ,
    validateflgs         text,
    valoverrideflgs      text,
    defaultvalue         text,
    bmrbpdbmatchid       text,
    bmrbpdbtransfunc     text,
    variabletypematch    text,
    entryidflg           char(1)      ,
    outputmapexistsflg   char(1)      ,
    aditautoinsert       integer      ,
    datumcountflgs       text,
    metadataflgs         char(1)      ,
    tagdeleteflgs        char(1)      ,
    example              text,
    help                 text,
    description          text,
    prompt               text
);

--
-- aditenumhdr table:
--
CREATE TABLE aditenumhdr (
    enumid               text NOT NULL,
    sfcategory           text NOT NULL,
    originaltag          text NOT NULL
);

--
-- aditenumdtl table:
--
CREATE  TABLE aditenumdtl (
    enumid               text NOT NULL,
    seq                  INTEGER,
    value                text NOT NULL,
    detail               text
);

--
-- aditcatgrp table:
--
CREATE  TABLE aditcatgrp (
    supergrpid          INTEGER NOT NULL,
    supergrpname        text NOT NULL,
    groupid             INTEGER,
    sfcategory          text primary key,
    mandatorynumber     INTEGER,
    aditreplicable      CHAR(5),
    allowuserfcode      CHAR(5),
    validateflgs        CHAR(10),
    aditviewflgs        CHAR(10),
    catgrpviewname      text NOT NULL,
    catgrpviewhelp      text
);

--
-- aditsupergrp table:
--
CREATE  TABLE aditsupergrp (
    supergrpid          INTEGER NOT NULL,
    supergrpname        text NOT NULL,
    viewflags           text NOT NULL,
    description         text
);

--
-- aditenumtie table:
--
CREATE  TABLE aditenumtie (
    categoryid          text NOT NULL,
    itemname            text NOT NULL,
    enumcategoryid      text NOT NULL,
    enumitemname        text NOT NULL
);

--
-- aditmanoverride table:
--
CREATE  TABLE aditmanoverride (
    orderofoperations    INTEGER NOT NULL,
    sfcategory           text NOT NULL,
    categoryid           text NOT NULL,
    itemname             text NOT NULL,
    newviewmandatorycode text NOT NULL,
    conditionalcatid     text,
    conditionalitemname  text,
    conditionalitemvalue text
);

--
-- nmrcifmatch table:
--
CREATE  TABLE nmrcifmatch (
    bmrbpdbmatchid        text,
    bmrbpdbtransfunc      text,
    tagcategory           text NOT NULL,
    tagfield              text NOT NULL,
    originaltag           text NOT NULL,
    variabletypematch     text,
    entryidflg            CHAR(1),
    outputmapexistsflg    CHAR(1)
);

--
-- validation links: information about conditional tags
--
CREATE  TABLE validationlinks (
    ctlsfcategory       text NOT NULL,
    ctltag              text,
    ctlvalue            text,
    depsfcategory       text NOT NULL,
    deptag              text NOT NULL,
    validateflags       VARCHAR(6) NOT NULL
);

--
-- validation overrides
--
create table validationoverrides (
    num		integer primary key,
    depsfcat	text,
    deptagcat	text,
    deptag	text,
    dbnullable	text,
    ctltagcat	text,
    ctltag	text,
    val		text
);

--
-- added 2012-03-09
--
-- "BMRB" types
--
create table ddltypes (
    ddltype text primary key,
    regexp text not null,
    description text
);

--
-- boilerplate comments
--
create table comments (
    comment text,
    everyflag char(1) not null default 'N',
    sfcategory text not null,
    tagname text
);


--
-- extra enumerations not in ADIT interface
--
create table val_enums (
    tagseq integer not null,
    val text not null
);

--
-- all enumerations: view
-- 
create view enumerations as select 
    t.dictionaryseq as seq,
    d.value as val
    from val_item_tbl t 
    join aditenumhdr h on h.originaltag=t.originaltag and h.sfcategory=t.originalcategory 
    join aditenumdtl d on d.enumid=h.enumid
    union select tagseq as seq, val
    from val_enums;

--
-- VALIDATION: tables that must have real data if saveframe exists
--
create view tag_cats as select
      distinct originalcategory as sfcategory,tagcategory from val_item_tbl
      where primarykey='Y' and loopflag='Y' and validateflgs like '%R';
