#!/usr/bin/python -u
#
# xlschem_ann.csv contains tag descriptions/definitions that are used soemwhere. we think.
# not sure if they aren't in NMR-STAR_internal.dic as well... or are different or what.
#
# tag name is col 8 and 
#
# the class is just a namespace wrapper really
#
from __future__ import absolute_import

import sys
import os
import sqlite3
import ConfigParser
import csv
import re
import pprint

if __package__ is None :
    __package__ = "nmr-star-dictionary-scripts"
    sys.path.append( os.path.abspath( os.path.join( os.path.split( __file__ )[0], ".." ) ) )
    from scripts import BaseClass as BaseClass
else :
    from . import BaseClass

#
#
#
class TagdefReader( BaseClass ) :

    """read xlschem_ann.csv into sqlite3 dictionary database"""

    SQL = "update adit_item_tbl set definition=:def where originaltag=:tag"

    # main
    #
    @classmethod
    def read_definitions( cls, props, connection = None, dburl = None, verbose = False ) :
        obj = cls( verbose = verbose )
        obj.config = props
        if connection is not None :
            obj.connection - connection
        else :
            obj.connect( url = dburl )
        csvdir = props.get( "dictionary", "csv.dir" )
        defile = props.get( "dictionary", "extras.tagdef_file" )
        infile = os.path.realpath( os.path.join( csvdir, defile ) )
        if not os.path.exists( infile ) :
            raise IOError( "File not found: %s" % (infile,) )
        with open( infile, "rU" ) as inf :
            in_table = False
            first_row = True
            tag_col = None
            val_col = None
            params = {}
            curs = obj.connection.cursor()
            rdr = csv.reader( inf )
            for row in rdr :
                if first_row :
                    for i in range( len ( row ) ) :
                        if row[i] == "Tag" : tag_col = i
                        if row[i] == "Dictionary description" : val_col = i
                    first_row = False
                    if (tag_col is None) or (val_col is None) :
                        raise Exception( "No Tag or Dictionary description column in 1st row" )
                    continue
                if row[0] == "TBL_BEGIN" :
                    in_table = True
                    continue
                if row[0] == "TBL_END" :
                    in_table = False
                    continue
                if not in_table :
                    continue
                if row[val_col] is None : continue
                val = str( row[val_col] ).strip()
                if val == "" : continue
                params.clear()
                params["tag"] = row[tag_col]

# should probably replace with comma rather than space...
#
                params["def"] = re.sub( r"\s+", " ", val.replace( "$", " " ) )
#                sys.stdout.write( "***\n" )
#                pprint.pprint( row )
#                sys.stdout.write( cls.SQL + "\n" )
#                pprint.pprint( params )
                curs.execute( cls.SQL, params )

            obj.connection.commit()
            curs.close()

        return obj

####################################################################################################
#
if __name__ == "__main__" :

    props = ConfigParser.SafeConfigParser()
    props.read( sys.argv[1] )
    dbfile = props.get( "dictionary", "sqlite3.file" )
    if not os.path.exists( dbfile ) :
        raise IOError( "File not found: %s (create dictionary first?)" % (dbfile,) )
    db = TagdefReader.read_definitions( props, dburl = dbfile, verbose = False )
