--
-- sqlite doesn't allow cascade in drop table statement
-- have to do this in proper order
--

drop view if exists enumerations;
drop view if exists tag_cats;
drop view if exists dict;
drop view if exists cat_grp;
drop view if exists val_item_tbl;
drop view if exists val_overrides;
drop view if exists val_enums;
drop view if exists printflags;
drop view if exists sfcats;

drop table if exists validator_sfcats;
drop table if exists validator_printflags;

drop table if exists aditenumtie;
drop table if exists aditenumdtl;
drop table if exists aditenumhdr;
drop table if exists extra_enumes;

drop table if exists aditmanoverride;
drop table if exists nmrcifmatch;
drop table if exists validationlinks;
drop table if exists validationoverrides;
drop table if exists query_inteface;

drop table if exists adit_item_tbl;
drop table if exists aditcatgrp;
drop table if exists aditsupergrp;

drop table if exists ddltypes;
drop table if exists comments;

--
-- these are for Eldon's CSV files
--
-- aditsupergrp table:
--

create table aditsupergrp (
    supergrpid          integer primary key,
    supergrpname        text not null unique,
    viewflags           text not null,
    description         text
);

--
-- aditcatgrp table:
--
create table aditcatgrp (
    supergrpid          integer not null,
    supergrpname        text not null,
    groupid             integer,
    sfcategory          text primary key,
    mandatorynumber     integer,
    aditreplicable      text,
    allowuserfcode      text,
    validateflgs        text,
    aditviewflgs        text,
    mandatorytagcats    text,
    catgrpviewname      text not null,
    catgrpviewhelp      text
--    ,
--    foreign key(supergrpid) references aditsupergrp(supergrpid),
--    foreign key(supergrpname) references aditsupergrp(supergrpname)
);

--
-- DICTIONARY TABLE
--
create table adit_item_tbl (
    dictionaryseq        integer primary key,
    originalcategory     text not null,
    aditcatmanflg        text not null,
    aditcatviewtype      text not null,
    aditsupercatid       text not null,
    aditsupercatname     text not null,
    aditcatgrpid         text not null,
    aditcatviewname      text,
    aditinitialrows      integer,
    originaltag          text not null unique,
    aditexists           text,
    aditviewflags        text not null,
    enumeratedflg        text,
    itemenumclosedflg    text,
    adititemviewname     text,
    aditformcode         integer,
    dbtype               text not null,
    bmrbtype             text,
    dbnullable           text,
    internalflag         text,
    rowIndexFlg          text,
    lclidflg             text,
    lclsfidflg           text,
    sfidflg              text,
    sfNameFlg            text,
    sfcategoryflg        text,
    sfPointerFlg         text,
    primarykey           text,
    foreignkeygroup      text,
    foreigntable         text,
    foreigncolumn        text,
    refkeygroup          text,
    reftable             text,
    refcolumn            text,
    indexflag            text,
    dbtablemanual        text,
    dbcolumnmanual       text,
    tagcategory          text not null,
    tagfield             text not null,
    loopflag             text,
    seq                  integer not null,
    dbflg                text,
    validateflgs         text,
    valoverrideflgs      text,
    defaultvalue         text,
    bmrbpdbmatchid       text,
    bmrbpdbtransfunc     text,
    variabletypematch    text,
    entryidflg           text,
    outputmapexistsflg   text,
    aditautoinsert       integer,
    datumcountflgs       text,
    metadataflgs         text,
    tagdeleteflgs        text,
    example              text,
    help                 text,
    description          text,
    prompt               text,
    definition           text,
    unique(tagcategory,tagfield)
--    ,foreign key(originalcategory) references aditcatgrp(sfcategory)
);

--
-- aditenumhdr table:
--
create table aditenumhdr (
    enumid               text primary key,
    sfcategory           text not null,
    originaltag          text not null
--    ,foreign key(sfcategory,originaltag) references adit_item_tbl(originalcategory,originaltag)
);

--
-- aditenumdtl table:
--
create table aditenumdtl (
    enumid               text not null,
    seq                  integer,
    value                text not null,
    detail               text
--    ,unique(enumid,value),
--    unique(enumid,seq),
--    foreign key(enumid) references aditenumhdr(enumid)
);

--
-- aditenumtie table:
-- (are foreign keys right?)
--
create table aditenumtie (
    categoryid          text not null,
    itemname            text not null,
    enumcategoryid      text not null,
    enumitemname        text not null
--    ,foreign key(categoryid,itemname) references adit_item_tbl(tagcategory,originaltag)
--    ,foreign key(enumcategoryid,enumitemname) references adit_item_tbl(tagcategory,originaltag)
);

--
-- aditmanoverride table:
--
create table aditmanoverride (
    orderofoperations    integer not null,
    sfcategory           text not null,
    categoryid           text not null,
    itemname             text not null,
    newviewmandatorycode text not null,
    conditionalcatid     text,
    conditionalitemname  text,
    conditionalitemvalue text
--    ,foreign key(sfcategory,categoryid,itemname) references adit_item_tbl(sfcategory,tagcategory,originaltag),
--    ,foreign key(conditionalcatid,conditionalitemname) references adit_item_tbl(tagcategory,originaltag)
);

--
-- TODO cleanu below
--

--
-- nmrcifmatch table:
--
CREATE  TABLE nmrcifmatch (
    bmrbpdbmatchid        VARCHAR(80),
    bmrbpdbtransfunc      VARCHAR(80),
    tagcategory           VARCHAR(80) NOT NULL,
    tagfield              VARCHAR(80) NOT NULL,
    originaltag           VARCHAR(80) NOT NULL,
    variabletypematch     VARCHAR(80),
    entryidflg            CHAR(1),
    outputmapexistsflg    CHAR(1)
);

--
-- validation links: information about conditional tags
--
CREATE  TABLE validationlinks (
    ctlsfcategory       VARCHAR(80) NOT NULL,
    ctltag              VARCHAR(80),
    ctlvalue            text,
    depsfcategory       VARCHAR(80) NOT NULL,
    deptag              VARCHAR(80) NOT NULL,
    validateflags       VARCHAR(6) NOT NULL
);

--
-- validation overrides
--
create table validationoverrides (
    num integer primary key,
    depsfcat varchar(90),
    deptagcat varchar(60),
    deptag varchar(90),
    dbnullable varchar(8),
    ctltagcat varchar(60),
    ctltag varchar(90),
    val text
);

--
-- added 2012-03-09
--
-- "BMRB" types
--
create table ddltypes (
    ddltype varchar(32) primary key,
    regexp varchar(384) not null,
    description text
);

--
-- boilerplate comments
--
create table comments (
    comment text,
    everyflag char(1) not null default 'N',
    sfcategory varchar(90) not null,
    tagname varchar(90)
--    ,foreign key(sfcategory) references aditcatgrp(sfcategory),
--    foreign key(tagname) references adit_item_tbl(originaltag)
);


--
-- extra enumerations not in ADIT interface
--
create table extra_enums (
    tagseq integer not null,
    val text not null
--    ,foreign key(tagseq) references adit_item_tbl(dictionaryseq)
);

--
-- query interface tags
--
create table query_interface (
    dictionaryseq integer, -- primary key,
    tagcategory varchar(60) not null,
    tagfield varchar(80) not null,
    taginterfaceflag varchar(10),
    prompt varchar(80),
    unique(tagcategory, tagfield)
--    ,foreign key(dictionaryseq) references adit_item_tbl(dictionaryseq),
--    foreign key(tagcategory,tagfield) references adit_item_tbl(tagcategory,tagfield)
);

--
-- all enumerations: view
-- 
create view enumerations as select 
    t.dictionaryseq as seq,
    d.value as val
    from adit_item_tbl t 
    join aditenumhdr h on h.originaltag=t.originaltag and h.sfcategory=t.originalcategory 
    join aditenumdtl d on d.enumid=h.enumid
    union select tagseq as seq, val
    from extra_enums;

--
-- VALIDATION: tables that must have real data if saveframe exists
--
-- create view tag_cats as select
--       distinct originalcategory as sfcategory,tagcategory from adit_item_tbl
--       where primarykey='Y' and loopflag='Y' and validateflgs like '%R';

create view tag_cats as select
    distinct sfcategory,mandatorytagcats as tagcategory from aditcatgrp
    where mandatorytagcats is not null;

--
-- renaming the table
--
create view dict as select * from adit_item_tbl;

--
-- new validator tables
--
-- reorder saveframes, add "non-public" and print/validate flags
--
create table validator_sfcats (
    sfcategory text not null unique,
    order_num integer not null,
    internalflag text not null,
    printflag text not null
--    ,foreign key(sfcategory) references aditcatgrp(sfcategory)
);

--
-- print flag for tags
--
create table validator_printflags (
    dictionaryseq integer not null,
    printflag text not null
--    ,foreign key(dictionaryseq) references adit_item_tbl(dictionaryseq)
);

--
-- views to mimic validator tables
--
create view printflags as select * from validator_printflags;
create view sfcats as select * from validator_sfcats;

create view cat_grp as 
    select v.order_num,v.order_num as groupid,v.sfcategory,
        case when upper(a.aditreplicable)='Y' then 'Y' else 'N' end as replicable,
        v.internalflag,v.printflag
    from validator_sfcats v join aditcatgrp a on a.sfcategory=v.sfcategory;

create view val_item_tbl as 
    select v.dictionaryseq,a.originalcategory,a.originaltag,a.tagcategory,a.tagfield,a.bmrbtype as ddltype,
        case when upper(a.dbtype) like 'DATE%' then 'DATE' else upper(a.dbtype) end as dbtype,
        case when upper(a.dbnullable)='NOT NULL' then 'N' else 'Y' end as dbnullable,
        case when upper(a.primarykey)='Y' then 'Y' else 'N' end as primarykey,
        a.refkeygroup,a.reftable,a.refcolumn,a.defaultvalue,
        case when upper(a.loopflag)='Y' then 'Y' else 'N' end as loopflag,
        case when upper(a.rowindexflg)='Y' then 'Y' else 'N' end as rowindexflag,
        case when upper(a.lclidflg)='Y' then 'Y' else 'N' end as localkeyflag,
        case when upper(a.lclsfidflg)='Y' then 'Y' else 'N' end as localsfidflag,
        case when upper(a.sfidflg)='Y' then 'Y' else 'N' end as sfidflag,
        case when upper(a.sfnameflg)='Y' then 'Y' else 'N' end as sfnameflag,
        case when upper(a.sfcategoryflg)='Y' then 'Y' else 'N' end as sfcategoryflag,
        case when upper(a.sfpointerflg)='Y' then 'Y' else 'N' end as sfpointerflag,
        case when upper(a.entryidflg)='Y' then 'Y' else 'N' end as entryidflag,
        case when a.datumcountflgs='?' then NULL else a.datumcountflgs end as datumcountflag,
        case when upper(a.itemenumclosedflg)='Y' then 'Y' else 'N' end as enumclosedflag,
        case when upper(a.internalflag)='Y' then 'Y' else 'N' end as internalflag,
        v.printflag
    from adit_item_tbl a join validator_printflags v on v.dictionaryseq=a.dictionaryseq;

create view val_overrides  as
    select ctltagcat,ctltag,val,
        case when upper(dbnullable)='NOT NULL' then 'N' else 'Y' end as dbnullable,
        depsfcat,deptagcat,deptag from validationoverrides
        where ctltag<>'_Entry_interview.BMRB_deposition'
        and ctltag<>'_Entry_interview.PDB_deposition'
        and deptag<>'*';

create view val_enums as 
    select seq as tagseq,val from enumerations 
    where val is not null and val<>'.' and val<>'?';

