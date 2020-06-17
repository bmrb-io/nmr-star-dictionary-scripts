#!/usr/bin/python -u
#
# create STAR files for "production" validator
#
#
#
from __future__ import absolute_import

import sys
import os
import sqlite3
import ConfigParser
import re
import pprint

if __package__ is None :
    __package__ = "nmr-star-dictionary-scripts"
    sys.path.append( os.path.abspath( os.path.join( os.path.split( __file__ )[0], ".." ) ) )
    from scripts import BaseClass as BaseClass, quote4star as quote4star
else :
    from . import BaseClass, quote4star

#
#
class ValidatorWriter( BaseClass ) :

    """Create dictionary file for interactive' validator"""

    TEXTTYPE = "TEXT" # "VARCHAR(10000)" # DB type for text fields -- needed to be varchar for oracle/older postgres

# mode is an index into a (6-) character string of flags. so we can have different ones.
# never used anything other than 0 & 1
#
#MODE = 1 # BMRB annotation
#MODE = 0 # BMRB released
#
# we don't use mode 0 anymore either as there's different code for releasing entries now
# filename for mode 1 is validict.3 -- for histerical raisins
# can set self._mode if need to, but you'll need to rename the output file afterwards
#
    DICTMODE = 1
    OUTFILE = "validict.3.str"

# tbles to print out
#
    TABLES = ["DATUMTYPES", "INFO", "SFCATS", "SFMANENUM", "STARCH", "TAGDEPS",
              "TAGMANENUM", "TAGRELS", "TAGS", "VALENUMS", "VALTYPENUM" ]

    # main
    #
    #
    @classmethod
    def create_validator_dictionary( cls, props, dburl = None, verbose = False ) :
        obj = cls( verbose = verbose )
        obj.config = props
        outdir = os.path.realpath( props.get( "validict", "output_dir" ) )
        if not os.path.isdir( outdir ) :
            os.makedirs( outdir )
        obj.connect()
        obj.create_tables()
        obj.attach( url = dburl )
        obj.make_info()
        obj.load_sfcats()
        obj.load_tags()
        obj.fix_loopmandatory()
#        obj._verbose = True
        obj.load_overrides()
#        obj._verbose = False
        obj.load_parent_child()
        obj.fix_experiment_names()
        obj.update_sf_links()
        obj.load_datum_types()
        obj.load_starch_table()
        obj.update_enums()
        obj.detach()

        if len( obj.errors ) > 0 :
            for e in obj.errors :
                sys.stderr.write( e + "\n" )

        obj.print_dictionary()

        return obj

    #
    #
    def __init__( self, *args, **kwargs ) :
        super( self.__class__, self ).__init__( *args, **kwargs )
        self._curs = None
        self._mode = self.DICTMODE
        self.errors = []

    # we attach the "main" db as a sub-schema
    #
    def connect( self ) :
        self._db = sqlite3.connect( ":memory:" )
        self._curs = self._db.cursor()
        self._curs2 = self._db.cursor()

    def attach( self, url ) :
        if url is None :
            assert isinstance( self._props, ConfigParser.SafeConfigParser )
            url = self._props.get( "dictionary", "sqlite3.file" )
        self._curs.execute( "attach '%s' as star" % (url,) )
#        self._db.isolation_level = None # -- do I need this anymore?

    # commit and detach main database 
    #
    def detach( self ) :
        self._db.commit()
        self._curs.execute( "detach star" )

####################################################################################################
    #
    #
    #
    def create_tables( self ) :
        if self._verbose : sys.stdout.write( self.__class__.__name__ + ".create_tables()\n" )

        ddl = self._props.get( "validict", "scriptfile" )
        with open( ddl, "rU" ) as fin :
            script = "".join( i for i in fin )
        self._curs.executescript( script )

####################################################################################################
    # fill version table
    # after create_tables() and attaching main DB
    #
    def make_info( self ) :
        if self._verbose : sys.stdout.write( self.__class__.__name__ + ".make_info()\n" )
        self._curs.execute( "delete from info" )
        self._curs.execute( "select defaultvalue from star.dict where originaltag='_Entry.NMR_STAR_version'" )
        row = self._curs.fetchone()
        if row is None : 
            raise Exception( "Error: no dictionary version" )

        self._curs.execute( "insert into info (dmode, version, dictflag) values (:mod,:vers,'Y')",
            { "mod" : self.DICTMODE, "vers" : str( row[0] ).strip() } )

####################################################################################################
    # Load saveframe categories table
    #
    def load_sfcats( self ) :
        if self._verbose : sys.stdout.write( self.__class__.__name__ + ".load_sfcats()\n" )

        qry = "select dictionaryseq from star.dict where originalcategory=:cat order by dictionaryseq limit 1"
        sql = "insert into sfcats (id,sfcat,uniq,mandatory) values (:id,:cat,:uniq,:man)"

        params = {}
        self._curs.execute( "select sfcategory,validateflgs,aditreplicable from aditcatgrp" )
        while True :
            params.clear()
            row = self._curs.fetchone()
            if row is None : break

# this is for sorting the saveframes in the "proper" tag order: order's different (wrong) in the source
#
            params["cat"] = row[0]
            self._curs2.execute( qry, params )
            if self.verbose :
                sys.stdout.write( qry + "\n" )
                pprint.pprint( params )
            seqrow = self._curs2.fetchone()
            if seqrow is None :
                raise Exception( "No dictionary sequence for category %s" % (row[0],) )
            if (seqrow is None) or (str( seqrow[0] ).strip()  == "") : 
                raise Exception( "Empty dictionary sequence for category %s" % (row[0],) )
            params["id"] = str( seqrow[0] ).strip()
            params["man"] = row[1].strip().upper()[self._mode:self._mode + 1]
            if row[2].strip().lower()[0:1] == "y" : params["uniq"] = "N"
            else : params["uniq"] = "Y"

            if self.verbose :
                sys.stdout.write( sql + "\n" )
                pprint.pprint( params )
            self._curs2.execute( sql, params )

####################################################################################################
    # Load tags table
    #
    def load_tags( self ) :
        if self._verbose : sys.stdout.write( self.__class__.__name__ + ".load_tags()\n" )

        sql = "insert into tags (seq,sfcat,tagname,tagcat,dbtable,dbcolumn,dbtype,dbnotnull," \
            + "dbpk,dbfktable,dbfkcolumn,dbfkgroup,valtype,valsize,mandatory,tagdepflag," \
            + "enumclosedflag,rowidxflag,localidflag,sfidflag,entryidflag,sflabelflag," \
            + "sfcatflag,sflinkflag,loopflag,loopmandatory,datumcount,metadata,deleteflag," \
            + "aditdefault,aditauto) values " \
            + "(:seq,:sfcat,:tag,:table,NULL,NULL,:dbtype,:notnull,:pk,:fktable,:fkcol,:fkgroup," \
            + ":type,:size,:man,NULL,:enumclosed,:rowidx,:localid,:sfid,:entryid,:sfname,:sfcatflag," \
            + ":sflink,:loop,NULL,:datumcnt,:metadata,:delete,:defval,:aditauto)"

        qry = "select dictionaryseq,originalcategory,originaltag,tagcategory,dbtype,dbnullable," \
            + "primarykey,foreigntable,foreigncolumn,foreignkeygroup,validateflgs," \
            + "itemenumclosedflg,rowindexflg,lclidflg,sfidflg,entryidflg,sfnameflg," \
            + "sfcategoryflg,sfpointerflg,loopflag,datumcountflgs,metadataflgs,tagdeleteflgs," \
            + "lclsfidflg,defaultvalue,aditautoinsert from star.dict order by dictionaryseq"

        varchar_pat = re.compile( r"char(?:\((\d+)\))?$", re.IGNORECASE )

        params = {}
        self._curs.execute( qry )
        while True :
            params.clear()
            row = self._curs.fetchone()
            if row is None : break

            params["seq"] = row[0]
            params["sfcat"] = row[1]
            params["tag"] = row[2]
            params["table"] = row[3]
            params["pk"] = row[6]
            params["fktable"] = row[7]
            params["fkcol"] = row[8]
            params["fkgroup"] = row[9]

# size only relevant for strings
# convert infomix types to postgres
#
            params["dbtype"] = row[4].lower()
            params["size"] = None
            params["type"] = "STRING"

            m = varchar_pat.search( params["dbtype"] )
            if m :
                params["size"] = m.group( 1 )
                if not params["size"].isdigit() :
                    raise Exception( "Error: value size is not a number for %s" % (row[2],) )
            elif params["dbtype"].find( "text" ) >= 0 : params["dbtype"] = self.TEXTTYPE
            elif params["dbtype"].find( "integer" ) >= 0 : params["type"] = "INTEGER"
            elif params["dbtype"].find( "float" ) >= 0 : params["type"] = "FLOAT"
            elif params["dbtype"].find( "real" ) >= 0 : params["type"] = "FLOAT"
            elif params["dbtype"].find( "date" ) >= 0 : 
                params["type"] = "DATE"
                params["dbtype"] = "DATE"

# NOT NULL: either not null or primary key
            params["notnull"] = None
            if (row[5] is not None) and (row[5].strip().lower()[0:1] == "n") : params["notnull"] = "N"
            if (row[6] is not None) and (row[6].strip().lower()[0:1] == "y") : params["notnull"] = "N"

            if row[10] is None :
                raise Exception( "Error: no mandatory flags for %s" % (row[2],) )
            params["man"] = row[10].strip().upper()[self._mode:self._mode + 1]

# Flags
# closed enumeration
#
            if row[11] is None : params["enumclosed"] = "N"
            elif row[11].strip().lower()[0:1] == "y" : params["enumclosed"] = "Y"
            else : params["enumclosed"] = "N"

# row index
#
            params["rowidx"] = "N"
            if (row[12] is not None) and (row[12].strip().lower()[0:1] == "y") : 
                params["rowidx"] = "Y"

# local id (key) for the table - not used

# global sf id
#
            params["sfid"] = "N"
            if (row[14] is not None) and (row[14].strip().lower()[0:1] == "y") : 
                params["sfid"] = "Y"

# entry id
#
            params["entryid"] = "N"
            if (row[15] is not None) and (row[15].strip().lower()[0:1] == "y") : 
                params["entryid"] = "Y"

# saveframe name (framecode)
#
            params["sfname"] = "N"
            if (row[16] is not None) and (row[16].strip().lower()[0:1] == "y") : 
                params["sfname"] = "Y"

# saveframe category flag
#
            params["sfcatflag"] = "N"
            if (row[17] is not None) and (row[17].strip().lower()[0:1] == "y") : 
                params["sfcatflag"] = "Y"

# not 'Y' for _label tags
# set default, fix later
#
            params["sflink"] = "N"

# saveframe pointer (framecode with $ in front)
#
            if (row[18] is not None) and (row[18].strip().lower()[0:1] == "y") : 
                params["type"] = "FRAMECODE"

# loop tag
#
            params["loop"] = "N"
            if (row[19] is not None) and (row[19].strip().lower()[0:1] == "y") : 
                params["loop"] = "Y"

# datum count
# these tags are for generating _Datum. loop
#
            params["datumcnt"] = "N"
            if (row[20] is not None) and (row[20].strip().lower()[0:1] == "y") : 
                params["datumcnt"] = "Y"

# metadata
# "interactive" validator does not load large data tables: too slow
#

            params["metadata"] = "N"
            if (row[21] is not None) and (row[21].strip().lower()[0:1] == "y") : 
                params["metadata"] = "Y"

# tag delete
# this is used for wide loops where most tags are not filled in. noramlly all loop tags are printed.
# added on annotators request
#
            params["delete"] = "N"
            if (row[22] is not None) and (row[22].strip().lower()[0:1] == "y") : 
                params["delete"] = "Y"

# local sf id
#
            params["localid"] = "N"
            if (row[23] is not None) and (row[23].strip().lower()[0:1] == "y") : 

# spec. case: exclude entry IDs in Entry from "insert local ids" editing function -- its local id
# is entry id and not the saveframe number

                if (row[2] != "_Entry.ID") and (row[2].find( ".Entry_ID" ) < 0) : 
                    params["localid"] = "Y"

# default value
# Entry ID is a unique-enough string used w/ search and replace
#
            params["defval"] = None
            if row[2].find( ".Entry_ID" ) >= 0 : params["defval"] = "NEED_ACC_NUM"
            elif row[24] is not None :
                params["defval"] = row[24].strip()
                if params["defval"] in ("?", ".") : params["defval"] = None

# autoinsert codes
#
# code 8 is saveframe label tag that has a matching _ID tag w/ code 7.
# it is "real data". other autoinsert codes are for automatically generated values that "aren't real"
# becasue we can re-create them anytime
#
            params["aditauto"] = "N"
            if row[25] is not None :
                if not str( params["aditauto"] ).isdigit() : pass
                if row[25] > 0 :
                    if row[25] != 8 :
                        params["aditauto"] = "Y"

            if self.verbose :
                sys.stdout.write( sql + "\n" )
                pprint.pprint( params )
            self._curs2.execute( sql, params )

# SF link flag
#
        sql = "update tags set sflinkflag='Y' where tagname=:tag"
        self._curs.execute( "select tagname from tags where valtype='FRAMECODE'" )
        while True :
            row = self._curs.fetchone()
            if row is None : break

            tag = row[0].replace( "_label", "_ID" )
            self._curs2.execute( sql, { "tag" : tag } )

# fixup, just in case
#
        self._curs2.execute( "update tags set aditauto='Y' where aditdefault is not null" )

####################################################################################################
    # If mandatory is V or M, select mandatory from sfcats where sfcat = ?
    # if sfcat is optional, reset to R or C resp. I.e.
    # "mandatory if saveframe exists" (R,C) vs. "mandatory always (implies: saveframe must exist)" (V,M)
    #
    def fix_loopmandatory( self ) :
        if self._verbose : sys.stdout.write( self.__class__.__name__ + ".fix_loopmandatory()\n" )

        sql = "update tags set mandatory=:man where seq=:seq"
        qry = "select mandatory from sfcats where sfcat=:sfcat"
        self._curs.execute( "select seq,sfcat,mandatory,tagname from tags where mandatory='V' or mandatory='M'" )
        params = {}
        while True :
            params.clear()
            row = self._curs.fetchone()
            if row is None : break

            params["seq"] = row[0]
            params["sfcat"] = row[1]
            if self.verbose :
                pprint.pprint( row )
                sys.stdout.write( qry + "\n" )
                pprint.pprint( params )
            self._curs2.execute( qry, params )
            sfrow = self._curs2.fetchone()
            if sfrow is None :
                raise Exception( "Error: no saveframe category for tag # %s", row[0] )
            if sfrow[0] == "O" :
                params["man"] = row[2]
                if params["man"] == "V" : params["man"] = "R"
                elif params["man"] == "M" : params["man"] = "C"
                self._curs2.execute( sql, params )

####################################################################################################
#
    # Mandatory overrides
    #
    def load_overrides( self ) :
        if self._verbose : sys.stdout.write( self.__class__.__name__ + ".load_overrides()\n" )
        ovrsql = "insert into tagdeps (ctlseq,ctlvalue,seq,mandatory) values (:ctseq,:ctval,:seq,:man)"
        tagsql = "update tags set tagdepflag='Y' where seq=:seq"
        qry = "select t1.dictionaryseq,v.ctlvalue,t2.dictionaryseq,v.validateflags,t1.originaltag " \
            + "from star.validationlinks v " \
            + "join star.dict t1 on t1.originalcategory=v.ctlsfcategory and t1.originaltag=v.ctltag " \
            + "join star.dict t2 on t2.originalcategory=v.depsfcategory and t2.originaltag=v.deptag"

        self._curs.execute( "select count(*) from star.validationlinks" )
        row = self._curs.fetchone()
        if row[0] < 1 :
            raise Exception( "empty validationlinks table" )

        self._curs.execute( "select count(*) from star.dict" )
        row = self._curs.fetchone()
        if row[0] < 1 :
            raise Exception( "empty dict table" )

        params = {}
        if self._verbose : 
            sys.stdout.write( qry )
            sys.stdout.write( "\n" )
        self._curs.execute( qry )
        while True :
            params.clear()
            row = self._curs.fetchone()
            if row is None : break

            if row[1] is not None :
                if row[1].strip() == "*" : continue # ADIT wildcard, not used by validator

            tag = row[4].strip()
            if tag in ("_Entry_interview.View_mode","_Entry_interview.PDB_deposition",
                    "_Entry_interview.BMRB_deposition") :
                continue # ADIT view-only tags

# let's not do that for now
#        if (tag == "_Entity.Number_of_monomers") and (row[1] == "polymer") : # Eldon's software can't 'V' this one
#            mandatory = "V"
#        else : 
            params["man"] = row[3].strip().upper()[self._mode:self._mode+1]

            params["ctseq"] = row[0]
            params["ctval"] = row[1]
            params["seq"] = row[2]

            if self._verbose : 
                sys.stdout.write( ovrsql )
                pprint.pprint( params )
            rc = self._curs2.execute( ovrsql, params )
            if self._verbose : 
                sys.stdout.write( "-- %s rows inserted\n" % (rc,) )

            if self._verbose : 
                sys.stdout.write( tagsql )
                pprint.pprint( params )
            rc = self._curs2.execute( tagsql, params )
            if self._verbose : 
                sys.stdout.write( "-- %s rows updated\n" % (rc,) )

####################################################################################################
#
    # Tag relationships
    # derived from foreign keys with no regard/support for compound keys
    #
    def load_parent_child( self ) :
        if self._verbose : sys.stdout.write( self.__class__.__name__ + ".load_parent_child()\n" )

        sql = "insert into tagrels (chldseq,prntseq) values (:childseq,:parentseq)"
        self._curs.execute( "select t1.dictionaryseq,t2.dictionaryseq from dict t1 " \
            + "join dict t2 on t2.tagcategory=t1.foreigntable and t2.tagfield=t1.foreigncolumn " \
            + "where t1.foreigntable is not null and t1.foreigncolumn is not null " \
            + "order by t2.dictionaryseq" )
        while True :
            row = self._curs.fetchone()
            if row is None : break

            self._curs2.execute( sql, { "childseq" : row[0], "parentseq" : row[1] } )

####################################################################################################
#
    # Turn off "enumclosed" flag for tags whose parent is _Experiment.Name
    #
    # Must run after load_parent_child()
    #
    def fix_experiment_names( self ) :
        if self._verbose : sys.stdout.write( self.__class__.__name__ + ".fix_experiment_names()\n" )
        sql = "update tags set enumclosedflag='N' where seq=:seq"
        self._curs.execute( "select r.chldseq from tagrels r join tags t on t.seq=r.prntseq " \
            + "where t.tagname='_Experiment.Name'" )
        while True :
            row = self._curs.fetchone()
            if row is None : break
            self._curs2.execute( sql, { "seq": row[0] } )

####################################################################################################
#
    # Saveframe link tags
    #
    def update_sf_links( self ) :
        if self._verbose : sys.stdout.write( self.__class__.__name__ + ".update_sflinks()\n" )

# match _label and _ID tags
# 
        sql = "update tags set sflinkflag='Y' where tagname=:tag"
        qry = "select seq from tags t join tagrels r on r.chldseq=t.seq where t.tagname=:tag"

        self._curs.execute( "select seq,tagname from tags where valtype='FRAMECODE'" )
        while True :
            row = self._curs.fetchone()
            if row is None : break

            if row[1].find( "_label" ) < 0 :
                self.errors.append( "tag %s does not end in '_label'" % (row[1],) )
                continue

            idtag = row[1].replace( "_label", "_ID" )
            self._curs2.execute( qry, { "tag" : idtag } )
            qrow = self._curs2.fetchone()
            if qrow is None :
                self.errors.append( "tag %s not found in related tags table. Missing foreign key?" % (idtag,) )
                continue

            self._curs2.execute( sql, { "tag" : idtag } )

# add _label to .Sf_framecode parent-child links
#
        sql = "insert into tagrels (prntseq,chldseq) values (:parent,:child)"
        qry = "select t1.tagcat from tags t1 join tagrels r on r.prntseq=t1.seq join tags t2 on t2.seq=r.chldseq " \
            + "where t2.tagname=:tag"
        qry1 = "select seq from tags where tagname=:tag"
        qry2 = "select prntseq,chldseq from tagrels where prntseq=:parent and chldseq=:child"

        self._curs.execute( "select seq,tagname from tags where valtype='FRAMECODE'" )
        while True :
            row = self._curs.fetchone()
            if row is None : break

            idtag = row[1].replace( "_label", "_ID" )
            self._curs2.execute( qry, { "tag" : idtag } )
            qrow = self._curs2.fetchone()
            if qrow is None : 
                self.errors.append( "parent tag for %s (%s) not found" % (idtag,row[1],) )
                continue

            fctag = "_" + qrow[0] + ".Sf_framecode"
            self._curs2.execute( qry1, { "tag" : fctag } )
            qrow = self._curs2.fetchone()
            if qrow is None :
                self.errors.append( "framecode tag %s (%s) not found" % (fctag,row[1],) )
                continue

# only add if not already there
#
            self._curs2.execute( qry2, { "parent" : qrow[0], "child" : row[0] } )
            qrow = self._curs2.fetchone()
            if qrow is None :
                self._curs2.execute( sql, { "parent" : qrow[0], "child" : row[0] } )

####################################################################################################
#
    # Datum types
    # This was supposed to drive table template generator on the website: tables whose tablegen flag is "y"
    # can be generated by that code. The list is in the properties file.
    #
    def load_datum_types( self ) :
        if self._verbose : sys.stdout.write( self.__class__.__name__ + ".load_datum_types()\n" )

        cats = self._props.get( "validict", "datum.categories" ).split()

        sql = "insert into datumtypes (tagcat,datumtype,tablegen) values (:table,:datum,:flag)"
        self._curs.execute( "select distinct tagcategory,datumcountflgs from star.dict " \
            + "where datumcountflgs is not null" )

        while True :
            row = self._curs.fetchone()
            if row is None : break

            flag = "N"
            if row[0] in cats : flag = "Y"

            self._curs2.execute( sql, { "table" : row[0], "datum" : row[1], "flag" : flag } )

####################################################################################################
#
    # this one's supposed to drive STARch PHP on the website. not that hard-coding it here is any
    # less work than hard-coding it there.
    #
    def load_starch_table( self ) :
        if self._verbose : sys.stdout.write( self.__class__.__name__ + ".load_starch_table()\n" )

        sql = "insert into starch (tagname,displname,displseq,rowidx,seqid,compidxid," \
            + "compid,atomid,atomtype,isotope,ambicode,val,minval,maxval,err,author," \
            + "tablegen,groupid) values (:tag,:label,:order,:idx,'N','N','N','N','N','N','N','N','N'," \
            + "'N','N','N','N',0)"

        qry = "select tagname,seq,rowidxflag from tags where metadata<>'Y' and tagname like :tag " \
            + "order by seq"

        curs3 = self._db.cursor()
        self._curs.execute( "select distinct tagcat from datumtypes where tablegen='Y'" )
        while True :
            row = self._curs.fetchone()
            if row is None : break

            tagname = "_" + row[0] + ".%%"
            self._curs2.execute( qry, { "tag" : tagname } )
            while True :
                qrow = self._curs2.fetchone()
                if qrow is None : break

                pos = qrow[0].find( "." )
                if pos >= 0 : taglabel = qrow[0][pos + 1:].replace( "_", " " )
                else : taglabel = "FIXME"

                curs3.execute( sql, { "tag" : qrow[0], "label" : taglabel, "order" : qrow[1], "idx" : qrow[2] } )

        self._curs.execute( "update starch set seqid='Y' where tagname like '%.Seq_ID%'" )
        self._curs.execute( "update starch set seqid='Y' where tagname like '%.Auth_seq_ID%'" )
        self._curs.execute( "update starch set author='Y' where tagname like '%.Auth_seq_ID%'" )
        self._curs.execute( "update starch set compidxid='Y' where tagname like '%.Comp_index_ID%'" )
        self._curs.execute( "update starch set compid='Y' where tagname like '%.Comp_ID%'" )
        self._curs.execute( "update starch set compid='Y' where tagname like '%.Auth_comp_ID%'" )
        self._curs.execute( "update starch set author='Y' where tagname like '%.Auth_comp_ID%'" )
        self._curs.execute( "update starch set atomid='Y' where tagname like '%.Atom_ID%'" )
        self._curs.execute( "update starch set atomid='Y' where tagname like '%.Auth_atom_ID%'" )
        self._curs.execute( "update starch set author='Y' where tagname like '%.Auth_atom_ID%'" )
        self._curs.execute( "update starch set atomtype='Y' where tagname like '%.Atom_type%'" )
        self._curs.execute( "update starch set isotope='Y' where tagname like '%.Atom_isotope_number%'" )
        self._curs.execute( "update starch set ambicode='Y' where tagname like '%.Ambiguity_code%'" )

        for i in range( 1, 7 ) :    
            self._curs.execute( "update starch set groupid=:id where tagname like :tag",
                { "id" : i, "tag" : ("%%_ID_%d" % (i,)) } )

        self._curs.execute( "update starch set val='Y' where tagname like '%.Val'" )
        self._curs.execute( "update starch set val='Y' where tagname like '%._val'" )
        self._curs.execute( "update starch set minval='Y' where tagname like '%.Val_min'" )
        self._curs.execute( "update starch set minval='Y' where tagname like '%._val_min'" )
        self._curs.execute( "update starch set maxval='Y' where tagname like '%.Val_max'" )
        self._curs.execute( "update starch set maxval='Y' where tagname like '%._val_max'" )
        self._curs.execute( "update starch set err='Y' where tagname like '%.Val_err'" )
        self._curs.execute( "update starch set err='Y' where tagname like '%._val_err'" )

####################################################################################################
#
    # enumerations
    #
    def update_enums( self ) :
        if self._verbose : sys.stdout.write( self.__class__.__name__ + ".update_enums()\n" )
        sql = "insert into valenums(seq,val) " \
            + "select seq,val from enumerations where val<>'?' and val<>'.' and val is not NULL"
        self._curs.execute( sql )

####################################################################################################
# output
#
    #
    #
    def print_table( self, table, out = sys.stdout ) :
        if self._verbose : sys.stdout.write( self.__class__.__name__ + ".print_table(%s)\n" % (table,) )

        self._curs.execute( "select count(*) from " + table )
        row = self._curs.fetchone()
        if row[0] < 1 :
            raise Exception( "Empty %s table" % (table,) )

        out.write( "    save_%s\n" % (table,) )
        out.write( "        loop_\n" )

        formats = []
        self._curs.execute( "select * from " + table )
        for i in self._curs.description :
            out.write( "            _%s\n" % (i[0],) )
            sql = "select max( length( %s ) ) from %s" % (i[0], table)
            self._curs2.execute( sql )
            row = self._curs2.fetchone()
            if row is None : 
                raise Exception( "Error: no field width for %s" % (i[0],) )

            fmt = "%"
            if row[0] > 0 : width = row[0] + 2
            else : width = 3
            fmt += "-%ds " % (width,)
            formats.append( fmt )

        out.write( "\n" )
        while True :
            row = self._curs.fetchone()
            if row is None : break
            for i in range( len( row ) ) :
                out.write( formats[i] % (quote4star( row[i] ),) )
            out.write( "\n" )

        out.write( "\n" )
        out.write( "        stop_\n" )
        out.write( "    save_\n\n" )

    # printout
    #
    def print_dictionary( self ) :
        if self._verbose : sys.stdout.write( self.__class__.__name__ + ".print()\n" )

        outdir = os.path.realpath( self._props.get( "validict", "output_dir" ) )
        if not os.path.isdir( outdir ) :
            raise IOError( "Directory not found: %s" % (outdir,) )

        outfile = os.path.join( outdir, self.OUTFILE )

        version = "3.1"
        self._curs.execute( "select version from info" )
        row = self._curs.fetchone()
        if row is None :
            raise Exception( "Error: no version in the dictionary!" )
        version = row[0]
        
        with open( outfile, "w" ) as out :
            out.write( "# this dictionary version is for the Java validator used by the annotators\n" )
            out.write( "# and ADIT-NMR post-processor\n" )
            out.write( "#\n" )
            out.write( "data_%s\n\n" % (version,) )

            for table in self.TABLES :
                self.print_table( table, out )
        
####################################################################################################
#
if __name__ == "__main__" :

    props = ConfigParser.SafeConfigParser()
    props.read( sys.argv[1] )
    dbfile = props.get( "dictionary", "sqlite3.file" )
    if not os.path.exists( dbfile ) :
        raise IOError( "File not found: %s (create dictionary first?)" % (dbfile,) )
    db = ValidatorWriter.create_validator_dictionary( props, dburl = dbfile, verbose = True )
