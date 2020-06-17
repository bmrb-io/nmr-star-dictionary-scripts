-- ****************************************************************************************
--
-- some day I'll clean this mess up...
--
-- validation dictionary
--

create view sfcats as select * from dict.validator_sfcats;
create view printflags as select * from dict.validator_printflags;
create view cat_grp as select * from dict.cat_grp;
create view ddltypes as select * from dict.ddltypes;
create view val_item_tbl as select * from dict.val_item_tbl;
create view adit_item_tbl as select * from dict.adit_item_tbl;
create view val_overrides  as select * from dict.val_overrides;
create view val_enums as select * from dict.val_enums;
create view comments as select * from dict.comments;
create view tag_cats as select * from dict.tag_cats;
