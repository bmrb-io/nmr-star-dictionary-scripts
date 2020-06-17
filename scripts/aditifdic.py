#!/usr/bin/python -u
#
# adit_interface_dict.txt contains extras used by adit-nmr: tag labels (interface prompts) and examples
#

from __future__ import absolute_import

import sys
import os
import sqlite3
import ConfigParser
import pprint
import re

if __package__ is None :
    __package__ = "nmr-star-dictionary-scripts"
    sys.path.append( os.path.abspath( os.path.join( os.path.split( __file__ )[0], ".." ) ) )
    from scripts import sas as sas
    from scripts import BaseClass as BaseClass
else :
    from . import sas
    from . import BaseClass

#
#
#
class DicParser( BaseClass, sas.ErrorHandler, sas.ContentHandler ) :

    """SAS handler for adit_interface_dict.txt"""

    SQL = "update adit_item_tbl set adititemviewname=:viewname,example=:example,description=:description " \
        + "where originaltag=:tag"

    # main
    #
    @classmethod
    def read_descriptions( cls, props, connection = None, dburl = None, verbose = False ) :
        obj = cls( verbose = verbose )
        obj.config = props
        if connection is not None :
            obj.connection = connection
        else :
            obj.connect( url = dburl )
        csvdir = props.get( "dictionary", "csv.dir" )
        descfile = props.get( "dictionary", "extras.adit_if_file" )
        infile = os.path.realpath( os.path.join( csvdir, descfile ) )
        if not os.path.exists( infile ) :
            raise IOError( "File not found: %s" % (infile,) )
        with open( infile, "rU" ) as inf :
            lex = sas.StarLexer( inf, bufsize = 0, verbose = verbose )
            sas.DdlParser.parse( lexer = lex, content_handler = obj, error_handler = obj, verbose = verbose )

        return obj

# _Adit_item_view_name appears to be redundant.
# Original code seems to add an extra blank line to that value and stick it in the database.
# See if this version breaks anything in adit -- seems not
    #
    #
    def __init__( self, *args, **kwargs ) :
        super( self.__class__, self ).__init__( *args, **kwargs )
        self._row = {}

# when reading csv excel does math on "1999-01-02" and gets 1996. Eldon adds a quote to defeat it
# so dates can survive round trips to csv and back
#
        self._date_re = re.compile( r"^\d{4}-\d{2}-\d{2}'" )
        self._curs = None

    # dot and question mark are nulls
    # replace dollar sign with comma: Excel doesn't quote strings when exporting CSV so input has $s instead
    #
    def _sanitize( self, val ) :
        if self._verbose : sys.stdout.write( self.__class__.__name__ + ".__sanitize()\n" )

        if val is None : return None
        v = str( val ).strip()
        if v == "" : return None
        if v in ("?", ".",) : return None
        return v.replace( "$", "," )

##########  SAS callbacks  ########################################################################

    def error( self, line, msg ) :
        sys.stderr.write( "parse error in line %d: %s\n" % (line,msg,) )
        return True
    def comment( self, line, text ) : return False
    def startLoop( self, line ) : return False
    def endLoop( self, line ) : return False

    def startData( self, line, name ) :
        if self._verbose : sys.stdout.write( self.__class__.__name__ + ".startData(%s)\n" % (name,) )
        if self._curs is None :
            self._curs = self._db.cursor()

#        self._curs.execute( "update dict set adititemviewname='n/a'" )
#        if self._verbose : print "zero out adititemviewnames:", self._curs.rowcount
        return False

    # commit and close -- __del__() is redundant
    #
    def endData( self, line, name ) :
        if isinstance( self._db, sqlite3.Connection ) :
            self._db.commit()
            self._curs.close()
            self._db.close()

    # every tag has its own saveframe: read into a dict and comit in endSaveframe()
    #
    def startSaveframe( self, line, name ) : 
        if self._verbose : sys.stdout.write( self.__class__.__name__ + ".startSaveframe(%s)\n" % (name,) )
        self._row.clear()
        return False

    #
    #
    def data( self, tag, tagline, val, valline, delim, inloop ) :
        if self._verbose : sys.stdout.write( self.__class__.__name__ + ".data()\n" )

        if tag == "_Tag" : 
            self._row["tag"] = val
            return False
        if tag == "_Description" :
            self._row["description"] = val
            return False
        if tag == "_Adit_item_view_name" :
            self._row["viewname"] = val
            return False

# FIXME: this is actually in loop but with only one value since it comes from main excel table.
# If that ever changes...
#
        if tag == "_Example" :
            m = self._date_re.search( val )
            if m : 
                val = val.rstrip( "'" )
            self._row["example"] = val
            return False

    # commit the tag
    #
    def endSaveframe( self, line, name ) :
        if self._verbose : sys.stdout.write( self.__class__.__name__ + ".endSaveframe(%s)\n" % (name,) )

# massage
#
        pprint.pprint( self._row )
        self._row["description"] = self._sanitize( self._row["description"] )
        self._row["example"] = self._sanitize( self._row["example"] )
        if self._verbose :
            sys.stdout.write( self.SQL + " " )
            pprint.pprint( self._row )
        self._curs.execute( self.SQL, self._row )
        if self._verbose : sys.stdout.write( ">>> %d rows\n" % (self._curs.rowcount,) )

        return False

####################################################################################################
#
if __name__ == "__main__" :

    props = ConfigParser.SafeConfigParser()
    props.read( sys.argv[1] )
    dbfile = props.get( "dictionary", "sqlite3.file" )
    if not os.path.exists( dbfile ) :
        raise IOError( "File not found: %s (create dictionary first?)" % (dbfile,) )
    db = DicParser.read_descriptions( props, dburl = dbfile, verbose = False )
