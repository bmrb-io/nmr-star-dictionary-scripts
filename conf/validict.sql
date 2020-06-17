--
-- dictionary
--

--
-- saveframe ctegories
--
drop table if exists cat_grp;
create table cat_grp (
    order_num integer primary key,
    groupid integer,
    sfcategory varchar(90) not null unique,
    replicable char(1) not null default 'N',
    internalflag char(1) not null default 'Y',
    printflag char(1) not null default 'O'
);

drop table if exists ddltypes;
create table ddltypes (
    ddltype varchar(32) primary key,
    regexp varchar(384) not null,
    description varchar(4096)
);

drop table if exists val_item_tbl;
create table val_item_tbl (
    dictionaryseq integer primary key,
    originalcategory varchar(90) not null,
    originaltag varchar(90) not null,
    tagcategory varchar(60) not null,
    tagfield varchar(80) not null,
    ddltype varchar(80) not null,
    dbtype varchar(20) not null,
    dbnullable char(1) not null default 'N',
    primarykey char(1) not null default 'N',
    refkeygroup varchar(255),
    reftable varchar(512),
    refcolumn varchar(512),
    defaultvalue varchar(255),
    loopflag char(1) not null default 'Y',
    rowindexflag char(1) not null default 'N',
    localkeyflag char(1) not null default 'N',
    localsfidflag char(1) not null default 'N',
    sfidflag char(1) not null default 'N',
    sfnameflag char(1) not null default 'N',
    sfcategoryflag char(1) not null default 'N',
    sfpointerflag char(1) not null default 'N',
    entryidflag char(1) not null default 'N',
    datumcountflag char(1) not null default 'N',
    enumclosedflag char(1) not null default 'N',
    internalflag char(1) not null default 'Y',
    printflag char(1) not null default 'O',
    unique( originalcategory, originaltag ),
    unique( tagcategory, tagfield ),
    foreign key (originalcategory) references catgrp (sfcategory)
        on delete cascade on update cascade,
    foreign key (ddltype) references ddltypes (ddltype)
        on delete cascade on update cascade
);

--
-- TODO: category to category overrides
--
drop table if exists val_overrides;
create table val_overrides (
    ctltagcat   varchar(90) not null,
    ctltag      varchar(90) not null,
    val         varchar(512) not null,
    dbnullable  char(1) not null default 'N',
    depsfcat    varchar(90) not null,
    deptagcat   varchar(90) not null,
    deptag      varchar(90) not null,
    foreign key( ctltagcat ) references val_item_tbl( tagcategory )
        on delete cascade on update cascade,
    foreign key( ctltag ) references val_item_tbl( originaltag )
        on delete cascade on update cascade,
    foreign key( depsfcat ) references val_item_tbl( originalcategory )
        on delete cascade on update cascade,
    foreign key( deptagcat ) references val_item_tbl( tagcategory )
        on delete cascade on update cascade,
    foreign key( deptag ) references val_item_tbl( originaltag )
        on delete cascade on update cascade
);

drop table if exists val_enums;
create table val_enums (
    tagseq integer not null,
    val varchar(512) not null,
    primary key( tagseq, val ),
    foreign key( tagseq ) references val_item_tbl( dictionaryseq )
        on delete cascade on update cascade
);

drop table if exists comments;
create table comments (
    comment varchar(1023),  -- not null,
    everyflag char(1) not null default 'N',
    sfcategory varchar(90) not null,
    tagname varchar(90),
    foreign key( sfcategory ) references catgrp( sfcategory )
        on delete cascade on update cascade
);

--
-- tables that must have real data if saveframe exists
--
drop table if exists tag_cats;
--create table tag_cats (
--    sfcategory varchar(90) not null,
--    tagcategory varchar(90) not null,
--    unique (sfcategory, tagcategory),
--    foreign key (sfcategory) references cat_grp (sfcategory)
--        on delete cascade on update cascade,
--    foreign key (tagcategory) references val_item_tbl (tagcategory)
--        on delete cascade on update cascade
--);
