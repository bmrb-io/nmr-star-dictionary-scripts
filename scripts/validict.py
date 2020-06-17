#!/usr/bin/python -u
#
# add tables for validator/pretty printer:
#  bits that aren't easy to get to in Eldon's files
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
class ValidatorDictionary( BaseClass ) :

    """Add/clean/reorder bits that validator is using"""

    DICTMODE = 1

    # main
    #
    #
    @classmethod
    def make_validator_tables( cls, props, connection = None, dburl = None, verbose = False ) :
        obj = cls( verbose = verbose )
        obj.config = props
        if connection is not None :
            obj.connection = connection
        else :
            obj.connect( url = dburl )
        obj.fill_sfcats_table()
        obj.fill_tags_table()
        obj.fixup()

        return obj

    #
    #
    def __init__( self, *args, **kwargs ) :
        super( self.__class__, self ).__init__( *args, **kwargs )
        self._mode = self.DICTMODE

    # saveframe categories
    #
    def fill_sfcats_table( self ) :
        if self._verbose : sys.stdout.write( self.__class__.__name__ + ".fill_sfcats_table()\n" )
        curs = self._db.cursor()

# just in case
#
        curs.execute( "delete from validator_sfcats" )

        sql =  "insert into validator_sfcats(sfcategory,order_num,internalflag,printflag) " \
            + "select s.sfcategory,1,'Y',substr(s.validateflgs,%s,1) from aditcatgrp s" % (str( self._mode ),)
        curs.execute( sql )

# saveframe categories are ordered differeently for adit-nmr
#
        cats = []
        sql = "update validator_sfcats set order_num=? where sfcategory=?"
        curs2 = self._db.cursor()
        qry = "select min(dictionaryseq),originalcategory from adit_item_tbl group by originalcategory"
        curs.execute( qry )
        while True :
            row = curs.fetchone()
            if row is None : break
            curs2.execute( sql, tuple( row ) )

# cache them for the next loop
#
            cats.append( row[1] )

# internal flag is 'Y' by default above
#
        sql = "update validator_sfcats set internalflag='N' where sfcategory=?"

# if all tags are Y this will return 0. if any one tag is not "internal", the whole category isn't
#
        qry = "select count(*) from adit_item_tbl where originalcategory=? " \
            + "and (internalflag is null or upper(internalflag)='N')"
        for dog in cats :
            curs.execute( qry, (dog,) )
            row = curs.fetchone()
            if row[0] > 0 :
                curs.execute( sql, (dog,) )

# "print" flag is both print and validate flags
# validation is at tag level, so validate flags aren't useful here except for the exception
#
# for printing all "invalid" categories should be "optional" and "internal"
#
        sql = "update validator_sfcats set printflag='O' where printflag='I'"
        curs.execute( sql )

# "mandatory" categories are "print even if there's no real data"
#
        sql = "update validator_sfcats set printflag='Y' where printflag='M'"
        curs.execute( sql )

# 'C' is a validation flag that means "at least one of these must be present in the entry"
# for printing 'C' = 'M' or 'O' (it implies there should be "real data" somewhere in there)
# 'C' for category is set in the last column of validate flags for the .Sf_category tag
#
        sql = "update validator_sfcats set printflag='C' where sfcategory=?"
        qry = "select originalcategory,upper(validateflgs) from adit_item_tbl where tagfield='Sf_category'"
        curs.execute( qry )
        while True :
            row = curs.fetchone()
            if row is None : break
            print "==>", row, "<==", row[1]
            if row[1][-1] == 'C' :
                curs2.execute( sql, (row[0],) )

        curs2.close()
        curs.close()

    # tags
    #
    def fill_tags_table( self ) :
        if self._verbose : sys.stdout.write( self.__class__.__name__ + ".fill_tags_table()\n" )
        curs = self._db.cursor()

# JIC
#
        sql = "delete from validator_printflags"
        curs.execute( sql )

        sql = "insert into validator_printflags (dictionaryseq,printflag) values (?,?)"
        curs2 = self._db.cursor()
        qry = "select dictionaryseq,upper(substr(validateflgs,%s,1))," % (str( self._mode )) 
        qry += "loopflag,tagdeleteflgs,tagcategory,tagfield from adit_item_tbl"
        curs.execute( qry )
        while True :
            row = curs.fetchone()
            if row is None : break
            flag = row[1]

# for printing "invalid" tags are optonal: no value no print
#
            if flag == "I" : flag = "O"

# "value required" are "print always", but value rquirement is deferred to NOT NULL instead
# mandatory tags are "print always" (even if it has no value)
#
            elif flag in ("M", "V") : flag = "Y"

# mandatory-conditional "R" and conditional "C" are as above "if saveframe exists"
# for printing this means: 
# - if a tag in the saveframe has real value, and so we're printing the saveframe, it's a "Y"
# - if we're not printing the saveframe, it's an "O"
# Can't make it work here, so just make them optional and if any of them have values: they'll get printed
#
            elif flag in ("C", "R") : flag = "O"

# all loop tags are "print always" except for the exceptions
#
            if (row[2] is not None) and (row[2] == "Y") :
                if (row[3] is not None) and (row[3] == "Y") :
                    flag = "N"

# free tags: these tables are broken and should be normalized
# until then make everythng optional and hope it works
#
            else :
                if (row[4] == "Entity") or (row[4] == "Citation") : 
                    flag = "O"

# ... unless it's Sf_ID
#
            if row[5] == "Sf_ID" :
                flag = "N"

# exceptional exceptions
#
            if (row[4] == "Upload_data") and (row[5] == "Data_file_immutable_flag") :
                flag = "N"
            if row[4] == "Entry_interview":
                if row[5] in ("PDB_deposition", "BMRB_deposition", "View_mode") :
                    flag = "N"

#            sys.stdout.write( "%s: %s, %s\n" % (sql, row[0], flag) )

            curs2.execute( sql, (row[0], flag) )

        curs2.close()
        curs.close()

    # misc. cleanups
    #
    def fixup( self ) :
        if self._verbose : sys.stdout.write( self.__class__.__name__ + ".fixup()\n" )
        curs = self._db.cursor()
        sql = "update adit_item_tbl set bmrbtype='line' where originaltag='_Upload_data.Data_file_Sf_category'"
        curs.execute( sql )
        curs.close()

####################################################################################################
#
if __name__ == "__main__" :

    props = ConfigParser.SafeConfigParser()
    props.read( sys.argv[1] )
    dbfile = props.get( "dictionary", "sqlite3.file" )
    if not os.path.exists( dbfile ) :
        raise IOError( "File not found: %s (create dictionary first?)" % (dbfile,) )
    db = ValidatorDictionary.make_validator_tables( props, dburl = dbfile, verbose = True )
