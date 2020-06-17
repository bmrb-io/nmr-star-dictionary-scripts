#!/usr/bin/python -u
#
# create dictionary files for ADIT-NMR:
#
# adit_nmr_upload_tags.csv
# bmrb_1.view
# default-entry.cif (actually this one's simply copied from Eldon's svn)
# dict.cif
# mmcif_bmrb.dic
# nmrcifmatch.cif
# table_dict.str
# View-bmrb.cif
#
#
from __future__ import absolute_import

import sys
import os
import sqlite3
import ConfigParser
import datetime
import shutil

if __package__ is None :
    __package__ = "nmr-star-dictionary-scripts"
    sys.path.append( os.path.abspath( os.path.join( os.path.split( __file__ )[0], ".." ) ) )
    from scripts import BaseClass as BaseClass
    from scripts import quote4star as quote4star
else :
    from . import BaseClass, quote4star

# Python rewrite of the "-ddl" part of Steve's create_schema_3
# High-level view is it's reformatting our stuff in the way ADIT will understand, but the details of
# ADIT are pretty much Double Dutch to me. So don't touch anything here, it was copy-pasted from
# Steve's code and we mostly don't know what it does or why.
#
class AditWriter( BaseClass ) :

# ADIT supports several "views" but we only use 1. Note that it's hardcoded in the bmrb_1.view filename
# in the .properties file
#
    VIEWMODE = 1

    ADITNMR_TYPES = {
        "DATETIME":        "date:yyyy-mm-dd",
        "FLOAT":           "floating-point",
        "DOUBLE PRECISION": "floating-point",
        "INTEGER":         "integer",
        "TEXT":            "text",
        "NCHAR(2)":        "2_characters_or_less",
        "VARCHAR(2)":      "2_characters_or_less",
        "CHAR(2)":         "2_characters_or_less",
        "NCHAR(3)":        "3_characters_or_less",
        "VARCHAR(3)":      "3_characters_or_less",
        "CHAR(3)":         "3_characters_or_less",
        "NCHAR(12)":       "12_characters_or_less",
        "VARCHAR(12)":     "12_characters_or_less",
        "CHAR(12)":        "12_characters_or_less",
        "NCHAR(15)":       "15_characters_or_less",
        "VARCHAR(15)":     "15_characters_or_less",
        "CHAR(15)":        "15_characters_or_less",
        "NCHAR(31)":       "31_characters_or_less",
        "VARCHAR(31)":     "31_characters_or_less",
        "CHAR(31)":        "31_characters_or_less",
        "VARCHAR(80)":    "80_characters_or_less",
        "CHAR(80)":       "80_characters_or_less",
        "NCHAR(80)":      "80_characters_or_less",
        "VARCHAR(127)":   "127_characters_or_less",
        "CHAR(127)":      "127_characters_or_less",
        "NCHAR(127)":     "127_characters_or_less",
        "VARCHAR(255)":   "255_characters_or_less",
        "CHAR(255)":      "255_characters_or_less",
        "NCHAR(255)":     "255_characters_or_less",
        "CHAR(1024)":   "1024_characters_or_less",
        "NCHAR(1024)":   "1024_characters_or_less",
        "VARCHAR(1024)":   "1024_characters_or_less",
        "NCHAR(2048)":   "2048_characters_or_less" ,
        "VARCHAR(2048)":   "2048_characters_or_less" 
    }

    TABLEDICT_COLS = [
        "dictionaryseq",
        "originalcategory",
        "aditCatManFlg",
        "aditCatViewType",
        "aditsupercatID",
        "aditsupercatName",
        "aditCatGrpID",
        "aditCatViewName",
        "aditInitialRows",
        "originaltag",
        "aditExists",
        "aditViewFlags",
        "enumeratedFlg",
        "itemEnumClosedFlg",
        "aditItemViewName",
        "aditFormCode",
        "dbtype",
        "bmrbtype",
        "dbnullable",
        "internalflag",
        "rowIndexFlg",
        "lclIDFlg",
        "lclSfIDFlg",
        "sfIDFlg",
        "sfNameFlg",
        "sfCategoryFlg",
        "sfPointerFlg",
        "primaryKey",
        "ForeignKeyGroup",
        "foreigntable",
        "foreigncolumn",
        "indexflag",
        "dbtablemanual",
        "dbcolumnmanual",
        "tagCategory",
        "tagField",
        "loopflag",
        "seq",
        "dbflg",
        "validateflgs",
        "valoverrideflgs",
        "defaultValue",
        "bmrbPdbMatchId",
        "bmrbPdbTransFunc",
        "variableTypeMatch",
        "entryIdFlg",
        "outputMapExistsFlg",
        "aditAutoInsert",
        "datumCountFlgs",
        "metaDataFlgs",
        "tagDeleteFlgs",
        "RefKeyGroup",
        "RefTable",
        "RefColumn",
        "example",
        "help",
        "description" ]

    NMRCIFMATCH_COLS = [
        "bmrbPdbMatchId",
        "bmrbPdbTransFunc",
        "tagCategory",
        "tagField",
        "originaltag",
        "variableTypeMatch",
        "entryIdFlg",
        "outputMapExistsFlg" ]

    # main
    #
    @classmethod
    def make_adit_files( cls, props, connection = None, dburl = None, verbose = False ) :
        obj = cls( verbose = verbose )
        obj.config = props
        outdir = os.path.realpath( props.get( "adit", "output_dir" ) )
        if not os.path.isdir( outdir ) :
            os.makedirs( outdir )
        if connection is None :
            obj.connect( url = dburl )
        else :
            obj.connection = connection
        obj.make_view_files()
        obj.make_dict_file()
        obj.copy_extra_files()
        obj.make_table_dict()
        obj.make_nmrcifmatch()
        return obj

    #
    #
    def __init__( self, *args, **kwargs ) :
        super( self.__class__, self ).__init__( *args, **kwargs )
        self._curs = None

#### temp view files ##########################################
# these methods return an open tmpfile descriptor, should probably change it to a stringbuffer
#
    # category groups: view file
    #
    def temp_view_category_groups( self ) :
        if self._verbose : sys.stdout.write( self.__class__.__name__ + ".temp_view_category_groups()\n" )

        out = os.tmpfile()
        out.write( """
#-------------- GROUP VIEWS -----------------
loop_
    _ndb_view_category_group.view_group_id
    _ndb_view_category_group.group_view_name
    _ndb_view_category_group.group_replicable
    _ndb_view_category_group.group_view_class
    _ndb_view_category_group.group_view_help_text
    _ndb_view_category_group.group_view_mandatory_code
    _ndb_view_category_group.group_view_display_code

""" )

        sql = "select g.sfCategory,g.catGrpViewName,g.aditReplicable,s.superGrpName,g.catGrpViewHelp," \
            + "g.aditViewFlgs,g.groupID " \
            + "from aditcatgrp g join aditsupergrp s on g.supergrpid = s.supergrpid " \
            + "order by g.groupID"
        curs = self.connection.cursor()
        curs.execute( sql )
        while True :
            row = curs.fetchone()
            if row is None : break

            if row[0] is None :
#                sfcat = "" # should never happen
                raise Exception( "No saveframe category in aditcatgrp!" )
            sfcat = str( row[0] ).strip()
            if sfcat == "" :
                raise Exception( "Saveframe category is an empty string in aditcatgrp!" )

            if row[1] is None : catgrpviewname = ""
            else : catgrpviewname = row[1].strip()

            if row[2] is None : aditreplicable = ""
            else : aditreplicable = row[2].strip()

            if row[3] is None : supergrpname = ""
            else : supergrpname = row[3].strip()

            if row[4] is None : catgrpviewhelp = ""
            else : catgrpviewhelp = row[4].strip()

            if row[5] is None : aditviewflgs = ""
            else : aditviewflgs = row[5][self.VIEWMODE - 1]

            out.write( """'%s'  '%s'  '%s'  '%s'
;
%s
;
    '%s'  'G0'
""" % (sfcat,catgrpviewname,aditreplicable,supergrpname,catgrpviewhelp,aditviewflgs) )

        curs.close()
        return out

###################################################
    # tag categories view file
    #
    def temp_view_categories( self ) :
        if self._verbose : sys.stdout.write( self.__class__.__name__ + ".temp_view_category_groups()\n" )

        out = os.tmpfile()

        out.write( """
#-------------- CATEGORY VIEWS --------------
loop_
    _ndb_view_category.category_id
    _ndb_view_category.category_view_name
    _ndb_view_category.view_group_id
    _ndb_view_category.category_view_mandatory_code
    _ndb_view_category.category_view_display_code
    _ndb_view_category.category_view_initial_rows

""" )

        sql = "select tagCategory,OriginalCategory,aditCatViewName,aditCatManFlg,aditCatViewType," \
            + "aditInitialRows,min(dictionaryseq) from dict " \
            + "where upper(dbFlg)='Y' and upper(aditExists)='Y'" \
            + "group by tagCategory order by min(dictionaryseq)"

        curs = self.connection.cursor()
        curs.execute( sql )
        while True :
            row = curs.fetchone()
            if row is None : break

            if row[0] is None : tagcategory = ""
            else : tagcategory = row[0].strip()

            if row[1] is None : originalcategory = ""
            else : originalcategory = row[1].strip()

            if row[2] is None : aditcatviewname = ""
            else : aditcatviewname = row[2].strip()

            if row[3] is None : aditcatmanflg = ""
            else : aditcatmanflg = row[3].strip()

            if row[4] is None : aditcatviewtype = ""
            else : aditcatviewtype = row[4].strip()

            if row[5] is None : aditinitialrows = 1
            else : aditinitialrows = int( str( row[5] ).strip() )

# Now the view file output:
            out.write( "'%s'\t" % (tagcategory) )
            out.write( """
;
%s
;
    """ % (aditcatviewname) )
            out.write( "'%s'\t" % (originalcategory) )
            out.write( "'%s'\t" % (aditcatmanflg) )
            out.write( "'%s'\n" % (aditcatviewtype) )
            out.write( "%d\n" % (aditinitialrows) )

        curs.close()
        return out

###################################################
    # tags: view file
    # Steve's code also generated sd_* (significant digits) columns for all floating fields.
    # We don't actually use them in 3.1, so I'm leaving that off.
    # (The logic is for any floafitng-pont tag, generate one called <category>._sd_<tag>
    # with flags set to H, Y, 1, N, N)
    #
    def temp_view_items( self ) :
        if self._verbose : sys.stdout.write( self.__class__.__name__ + ".temp_view_items()\n" )

        out = os.tmpfile()
        out.write( """
#--------------- ITEM VIEWS -----------------
loop_
    _ndb_view_item.category_id
    _ndb_view_item.item_name
    _ndb_view_item.item_view_name
    _ndb_view_item.item_view_mandatory_code
    _ndb_view_item.item_view_allow_alternate_value
    _ndb_view_item.item_view_form_code
    _ndb_view_item.item_sf_id_flag
    _ndb_view_item.item_sf_name_flag

""" )

        sql = "select tagcategory,tagfield,adititemviewname,description,aditviewflags,itemEnumClosedFlg," \
            + "aditformcode,sfidflg,sfNameflg,dictionaryseq from dict " \
            + "where upper(dbFlg)='Y' and upper(aditExists)='Y' " \
            + "order by tagcategory,dictionaryseq"

        curs = self.connection.cursor()
        curs.execute( sql )
        while True :
            row = curs.fetchone()
            if row is None : break

            if row[0] is None : tagcategory = ""
            else : tagcategory = row[0].strip()

            if row[1] is None : tagfield = ""
            else : tagfield = row[1].strip()

            if row[2] is None : adititemviewname = ""
            else : adititemviewname = row[2].strip()

            if row[3] is None : description = ""
            else : description = row[3].strip()

            if (adititemviewname == "na") or (adititemviewname == "") :
                adititemviewname = description

            if row[4] is None : aditviewflag = ""
            else : aditviewflag = row[4][self.VIEWMODE - 1]

# flip this flag because it's the other way around in adit dictionary.
# apparently.
#
            if row[5] is None : enumclosedflag = "Y"
            elif str( row[5] ).strip().upper() == "Y" : enumclosedflag = "N"
            else : enumclosedflag = "Y"

            if row[6] is None : formcode = ""
            else : formcode = int( str( row[6] ).strip() )

            if row[7] is None : sfidflag = "N"
            elif str( row[7] ).strip().upper() == "Y" : sfidflag = "Y"
            else : sfidflag = "N"

            if row[8] is None : sflabelflag = "N"
            elif str( row[8] ).strip().upper() == "Y" : sflabelflag = "Y"
            else : sflabelflag = "N"

            out.write( "    '%s'\t" % (tagcategory) )
            out.write( "'_%s.%s'\t" % (tagcategory,tagfield) )

            out.write( """
;
%s
;
    """ % (adititemviewname) )

            out.write( "'%s'\t" % (aditviewflag) )
            out.write( "'%s'\t" % (enumclosedflag) )
            out.write( "%d\t" % (formcode) )
            out.write( "'%s'\t" % (sfidflag) )
            out.write( "'%s'\n" % (sflabelflag) )

        curs.close()
        return out

###################################################
    # mandatory overrides
    #
    def temp_view_man_overrides( self ) :
        if self._verbose : sys.stdout.write( self.__class__.__name__ + ".temp_view_category_groups()\n" )

        out = os.tmpfile()
        out.write( """
#-------------- MANDATORY CODE OVERRRIDE ----------------
loop_
    _mandatory_code_override.group
    _mandatory_code_override.category_id
    _mandatory_code_override.item_name
    _mandatory_code_override.new_view_mandatory_code
    _mandatory_code_override.conditional_category_id
    _mandatory_code_override.conditional_item_name
    _mandatory_code_override.conditional_item_value

""" )


        sql = "select orderOfOperations,sfcategory,categoryId,itemName,newViewMandatoryCode," \
            + "conditionalCatId,conditionalItemName,conditionalItemValue from aditmanoverride " \
            + "order by orderOfOperations"

        curs = self.connection.cursor()
        curs.execute( sql )
        while True :
            row = curs.fetchone()
            if row is None : break

            if row[1] is None : sfcat = ""
            else : sfcat = row[1].strip()

            if row[2] is None : categoryid = ""
            else : categoryid = row[2].strip()

            if row[3] is None : itemname = ""
            else : itemname = row[3].strip()

            if row[4] is None : newviewmandatorycode = ""
            else : newviewmandatorycode = row[4].strip()

            if row[5] is None : conditionalcatid = "*"
            else : conditionalcatid = row[5].strip()

            if row[6] is None : conditionalitemname = "*"
            else : conditionalitemname = row[6].strip()

            if row[7] is None : conditionalitemvalue = "*"
            else : conditionalitemvalue = row[7].strip()

            out.write( "'%s'  '%s'  '%s'  '%s'  '%s'  '%s'  '%s'\n" % 
                (sfcat,categoryid,itemname,newviewmandatorycode,conditionalcatid,conditionalitemname,conditionalitemvalue) )

        curs.close()
        return out

###################################################
    # enumerations
    #
    def temp_view_enum_ties( self ) :
        if self._verbose : sys.stdout.write( self.__class__.__name__ + ".temp_view_enum_ties()\n" )

        out = os.tmpfile()
        out.write( """
#-------------- ENUMERATION TIES ----------------
loop_
    _enumeration_ties.category_id
    _enumeration_ties.item_name
    _enumeration_ties.enum_category_id
    _enumeration_ties.enum_item_name

""" )

        sql = "select categoryId,itemName,enumCategoryId,enumItemName from aditenumtie " \
            + "order by itemName,enumCategoryId"

        curs = self.connection.cursor()
        curs.execute( sql )
        while True :
            row = curs.fetchone()
            if row is None : break

            if row[0] is None : categoryid = ""
            else : categoryid = row[0].strip()

            if row[1] is None : itemname = ""
            else : itemname = row[1].strip()

            if row[2] is None : enumcategoryid = ""
            else : enumcategoryid = row[2].strip()

            if row[3] is None : enumitemname = ""
            else : enumitemname = row[3].strip()

            out.write( "'%s'  '%s'  '%s'  '%s'\n" % (categoryid,itemname,enumcategoryid,enumitemname) )

        curs.close()
        return out

########################## output ####################
    # two output files are identical except for the name
    #
    def make_view_files( self ) :
        if self._verbose : sys.stdout.write( self.__class__.__name__ + ".make_view_files()\n" )
        
        outdir = self._props.get( "adit", "output_dir" )
        onefile = self._props.get( "adit", "supergroupfile" )
        twofile = self._props.get( "adit", "viewfile" )

        outfile = os.path.realpath( os.path.join( outdir, onefile ) )
        viewfile = os.path.realpath( os.path.join( outdir, twofile ) )

        with open( outfile, "wb" ) as out :
            out.write( """######################################################
#   View file from BMRB dictionary.
#   This file is generated automatically, don't edit.
######################################################
#   Creation ran on: %s
######################################################
data_viewbmrb

""" % (datetime.date.today().isoformat()) )

            for fn in (self.temp_view_category_groups, self.temp_view_categories, self.temp_view_items,
                    self.temp_view_man_overrides, self.temp_view_enum_ties) :
                tmp = fn()
                tmp.seek( 0 )
                for line in tmp :
                    out.write( line )
                tmp.close()

        shutil.copy( outfile, viewfile )

###################################################

    # MMCIF .dic file
    # Steve's original prints this to stdout and runs with "> mmcif_bmrb.dic"
    #
    def make_dict_file( self ) :
        if self._verbose : sys.stdout.write( self.__class__.__name__ + ".make_dict_file()\n" )
        outdir = self._props.get( "adit", "output_dir" )
        onefile = self._props.get( "adit", "dictfile" )
        outfile = os.path.realpath( os.path.join( outdir, onefile ) )
        with open( outfile, "wb" ) as out :

# boilerplate prefix -- I guess this was copied verbatim from some earlier dictionary file...
#
            out.write( """###############################################
#   BMRB NMRSTAR-AS-RELATIONS in a CIF-LIKE   #
#   DICTIONARY (in DDL syntax)                #
###############################################

data_cif_bmrb.dic


######################
#   ITEM TYPE LIST   #
######################
# Please note that these types were taken directly from
# Database field types in ANSI SQL syntax.

    loop_
        _item_type_list.code
        _item_type_list.primitive_code
        _item_type_list.construct
        _item_type_list.detail

        # - John - why did you say this was a mistake last time?

        'date:yyyy-mm-dd'
        char
        '[0-9][0-9][0-9][0-9][-/][0-9][0-9][-/][0-9][0-9]'
        'date in YYYY-MM-DD format'

        'floating-point'
        numb
        '[-+]{0,1}(([0-9]+)|([0-9]*\.[0-9]+))([eE][+-]?[0-9]+){0,1}'
        'number, floating point and exponential notation allowed.'

        'floating-point'
        numb
        '[-+]{0,1}(([0-9]+)|([0-9]*\.[0-9]+))([eE][+-]?[0-9]+){0,1}'
        'number, floating point and exponential notation allowed.'

        'integer'
        numb
        '[-+]{0,1}[0-9]+'
        'number, must be an integer.'

        '2_characters_or_less'
        char
        '.{0,2}'
        'A string value, not allowed to exceed 2 characters.'

        '3_characters_or_less'
        char
        '.{0,3}'
        'a small string, at most 3 characters'

        '12_characters_or_less'
        char
        '.{0,12}'
        'a small string, at most 12 characters'

        '15_characters_or_less'
        char
        '.{0,15}'
        'A string value, not allowed to exceed 15 characters.'

        '31_characters_or_less'
        char
        '.{0,31}'
        'A string value, not allowed to exceed 31 characters.'

        '80_characters_or_less'
        char
        '.{0,80}'
;       A string value, not allowed to exceed 80 characters.
        Typically used in internal boilerplate fields
;

        '127_characters_or_less'
        char
        '.{0,127}'
        'A string value, not allowed to exceed 127 characters.'

        '255_characters_or_less'
        char
        '.{0,255}'
        'A string value, not allowed to exceed 255 characters.'

        '1024_characters_or_less'
        char
        '.{0,1024}'
        'A string value, not allowed to exceed 1024 characters.'

        'text'
        char
        '.*'
        'A string value, allowed to be rather long (many lines).'

    # stop_ commented out

""" )

# category groups
#
            sql = "select sfCategory,min(groupID) from aditcatgrp group by sfCategory order by min(groupID)"
            curs = self.connection.cursor()
            curs.execute( sql )

            out.write( """
#----------------------------
#  CATEGORY_GROUP_LIST
#----------------------------

loop_
    _category_group_list.id
    _category_group_list.parent_id
    _category_group_list.description

""" )

            while True :
                row = curs.fetchone()
                if row is None : break

                if row[0] is None : sfcat = "" # should never happen
                else : sfcat = row[0].strip()
                out.write( """        '%s'
        .
;
%s
;
""" % (sfcat, sfcat) )

# categories and tags together
#
            sql = "select tagCategory,OriginalCategory,upper(LoopFlag),min(dictionaryseq) from dict " \
                + "where upper(dbFlg)='Y' and upper(aditExists)='Y' " \
                + "group by tagCategory order by min(dictionaryseq)"

            sql2 = "select tagField,description,dbnullable,defaultValue,dbtype,example,dictionaryseq " \
                + "from dict where tagcategory=:tagcat and upper(dbFlg)='Y' and upper(aditExists)='Y' " \
                + "order by dictionaryseq"

            sql3 = "select d.value,d.detail,d.seq from aditenumhdr h join aditenumdtl d " \
                + "on d.enumid=h.enumid where h.originaltag=:tag order by d.seq"

            curs2 = self.connection.cursor()
            curs3 = self.connection.cursor()

            curs.execute( sql )
            while True :
                row = curs.fetchone()
                if row is None : break

                if row[0] is None : tagcategory = ""
                else : tagcategory = row[0].strip()

                if row[1] is None : originalcategory = ""
                else : originalcategory = row[1].strip()

                if row[2] is None : loopflag = False
                elif str( row[2] ).strip() == "Y" : loopflag = True
                else : loopflag = False

# dict file output
#
                out.write( """
# ----------------------------------------------------------
# Category %s
#    (original_category = %s)
# ----------------------------------------------------------

save_%s  #(Category)

    _category.description""" % (tagcategory,originalcategory,tagcategory) )

                if loopflag :
                    out.write( """
;
    This category is a loop within NMRSTAR.
    (TODO: fill in with a more descriptive message)
;
""" )
                else :
                    out.write( """
;
    This category represents free tags within NMRSTAR.
    (TODO: fill in with a more descriptive message)
;
""" )
                out.write( """
    _category.id                '%s'
    _category.mandatory_code    'no'""" % (tagcategory) )

                if loopflag :
                    out.write( """
    # This is a combined key in the database - I am not
    # sure if this is  the right way to express it in
    # DDL or not:
    loop_
   _category_key.name
   '_%s.Sf_ID'
   '_%s.loopseq'
    # stop_ commented out
""" % (tagcategory,tagcategory) )
                else :
                    out.write( """
    _category_key.name      '_%s.Sf_ID'
""" % (tagcategory) )

                out.write( "save_\n\n" )

# tag details
#
                curs2.execute( sql2, { "tagcat" : tagcategory } )
                while True :
                    row2 = curs2.fetchone()
                    if row2 is None : break

                    if row2[0] is None : tagfield = ""
                    else : tagfield = str( row2[0] ).strip()

                    if row2[1] is None : description = "?"
                    else : description = row2[1].strip()

                    if row2[2] is None : mandatory_code = "yes"
                    elif row2[2].strip().upper() == "NOT NULL" : mandatory_code = "no"
                    else : mandatory_code = "yes"

                    if row2[3] is None : default_val = "?"
                    else : default_val = quote4star( row2[3].strip() )

                    if row2[4] is None : adit_type = "?"
                    elif row2[4][:8].strip().upper() == "DATETIME" : adit_type = "DATETIME"
                    elif row2[4][:7].strip().upper() == "BOOLEAN" : adit_type = "3_characters_or_less"
                    elif (row2[4].upper().find( "CHAR" ) != -1) and not (row2[4].strip().upper() in self.ADITNMR_TYPES) :
                        adit_type = "text"
                    else : adit_type = self.ADITNMR_TYPES[row2[4].strip().upper()]

                    if row2[5] is None : example = None
                    else : example = quote4star( row2[5].strip() )

                    out.write( "save__%s.%s\n" % (tagcategory,tagfield) )
                    out.write( """    _item_description.description
;
%s
;
""" % (description) )
                    out.write( "    _item.category_id      '%s'\n" % (tagcategory) )
                    out.write( "    _item.mandatory_code   '%s'\n" % (mandatory_code) )
                    out.write( "    _item_default.value    %s\n" % (default_val) )
                    out.write( "    _item_type.code        '%s'\n" % (adit_type) )
                    if example is not None :
                        out.write( """
    loop_
        _item_examples.case
        _item_examples.detail

        .
;
%s
;
""" % (example) )

# now check enums
#
                    tag = "_%s.%s" % (tagcategory,tagfield)
                    header_printed = False
                    curs3.execute( sql3, {"tag" : tag } )
                    while True :
                        row3 = curs3.fetchone()
                        if row3 is None : break

                        if row3[0] is None : enum_val = None
                        else : enum_val = row3[0].strip()

                        if row3[1] is None : enum_dtl = None
                        else : enum_dtl = row3[1].strip()

                        if (enum_val is None) and (enum_dtl is None) : continue

                        if not header_printed :
                            out.write( """
    loop_
        _item_enumeration.value
        _item_enumeration.detail

""" )
                            header_printed = True

                        out.write( """    '%s\'
;
%s
;
""" % (enum_val,enum_dtl) )

# closing save_ at tag level
#
                    out.write( "save_\n\n" )

            curs3.close()
            curs2.close()
            curs.close()

####################################################################################################

    # extra files should be just copied over but they come with a mixture of macwindows line endings,
    # permission bits, lack of trailing newlines etc.
    #
    def copy_extra_files( self ) :
        outdir = self._props.get( "adit", "output_dir" )
        csvdir = self._props.get( "dictionary", "csv.dir" )
        onefile = self._props.get( "adit", "extras.default_entry" )

        outfile = os.path.realpath( os.path.join( outdir, onefile ) )
        infile = os.path.realpath( os.path.join( csvdir, onefile ) )
        if not os.path.exists( infile ) :
            raise IOError( "File not found: %s" % (infile,) )

        with open( outfile, "w" ) as out :
            with open( infile, "rU" ) as fin :
                for line in fin :
                    out.write( line.rstrip() )
                    out.write( "\n" )

        twofile = self._props.get( "adit", "extras.data_categories" )
        outfile = os.path.realpath( os.path.join( outdir, twofile ) )
        infile = os.path.realpath( os.path.join( csvdir, twofile ) )
        if not os.path.exists( infile ) :
            raise IOError( "File not found: %s" % (infile,) )

        with open( outfile, "w" ) as out :
            with open( infile, "rU" ) as fin :
                for line in fin :
                    out.write( line.rstrip() )
                    out.write( "\n" )

####################################################################################################

    # these two are almost identical. almost
    #
    def make_table_dict( self ) :

        outdir = self._props.get( "adit", "output_dir" )
        onefile = self._props.get( "adit", "tabledict.cif" )
        twofile = self._props.get( "adit", "tabledict.str" )

        ciffile = os.path.realpath( os.path.join( outdir, onefile ) )
        strfile = os.path.realpath( os.path.join( outdir, twofile ) )

        with open( ciffile, "wb" ) as cifout :
            with open( strfile, "wb" ) as strout :

                cifout.write( "data_dict\n" )
                cifout.write( "loop_\n\n" )

                strout.write( "data_val_item_tbl_o.csv\n" )
                strout.write( "loop_\n\n" )

                for tag in self.TABLEDICT_COLS :
                    cifout.write( "    _dict.%s\n" % (tag,) )
                    strout.write( "    _%s\n" % (tag,) )

                cifout.write( "\n\n" )
                strout.write( "\n\n" )

                sql = "select "
                sql += ",".join( i for i in self.TABLEDICT_COLS )
                sql += " from dict order by dictionaryseq"

                curs = self.connection.cursor()
                curs.execute( sql )
                while True :
                    row = curs.fetchone()
                    if row is None : break
                    for i in range( len( row ) ) :
                        if (i == 56) or (i == 57) : val = "."    # omit for brevity

# soem of them have trailing newlines that quote() preserves
#
                        elif row[i] is None : val = "."
                        else : val = quote4star( str( row[i] ).strip() )

                        cifout.write( "  %s" % (val,) )
                        strout.write( "  %s" % (val,) )

                    cifout.write( "\n" )
                    strout.write( "\n" )

                curs.close()

####################################################################################################
    #
    #
    def make_nmrcifmatch( self ) :
        outdir = self._props.get( "adit", "output_dir" )
        onefile = self._props.get( "adit", "nmrcifmatchfile" )
        ciffile = os.path.realpath( os.path.join( outdir, onefile ) )
        with open( ciffile, "wb" ) as out :

            curs = self.connection.cursor()
            out.write( "data_nmrcifmatch\n" )
            out.write( "loop_\n\n" )
            formats = []
            for tag in self.NMRCIFMATCH_COLS :
                out.write( "    _nmrcifmatch.%s\n" % (tag,) )

# this is just for pretty-printing
#
                sql = "select max(length(%s)) from dict" % (tag,)
                curs.execute( sql )
                row = curs.fetchone()
                if row is None : 
                    raise Exception( "Error: no field width for %s" % (tag,) )
                fmt = "%"
                if row[0] > 0 : width = row[0] + 2
                else : width = 3
                fmt += "-%ds " % width
                formats.append( fmt )

            out.write( "\n\n" )

            sql = "select "
            sql += ",".join( i for i in self.NMRCIFMATCH_COLS )
            sql += " from nmrcifmatch" # order by originaltag"
            curs.execute( sql )
            while True :
                row = curs.fetchone()
                if row is None : break
                for i in range( len( row ) ) : 
                    out.write( formats[i] % quote4star( row[i] ) )
                out.write( "\n" )

            curs.close()

####################################################################################################
#
if __name__ == "__main__" :

    props = ConfigParser.SafeConfigParser()
    props.read( sys.argv[1] )
    dbfile = props.get( "dictionary", "sqlite3.file" )
    if not os.path.exists( dbfile ) :
        raise IOError( "File not found: %s (create dictionary first?)" % (dbfile,) )
    db = AditWriter.make_adit_files( props, dburl = dbfile, verbose = False )
