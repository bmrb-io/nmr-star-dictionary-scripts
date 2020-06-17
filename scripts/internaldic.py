#!/usr/bin/python -u
#
# NMR-STAR_internal.dic contains most, but not all of the dictionary info.
# E.g. what's used by adit-nmr is not there and has to be read from the csv files.
# So ATM we only read the DDL types table from this file.
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
    from scripts import sas as sas
    from scripts import BaseClass as BaseClass
else :
    from . import sas
    from . import BaseClass

#
#
#
class DicParser( BaseClass, sas.ErrorHandler, sas.ContentHandler ) :

    """SAS parser for NMR-STAR_internal.dic"""

    SQL = "insert into ddltypes(ddltype,regexp,description) values (:type,:re,:detail)"

    # main
    #
    @classmethod
    def read_ddltypes( cls, props, connection = None, dburl = None, verbose = False ) :
        obj = cls( verbose = verbose )
        obj.config = props
        if connection is not None :
            obj.connection = connection
        else :
            obj.connect( url = dburl )
        csvdir = props.get( "dictionary", "csv.dir" )
        dicfile = props.get( "dictionary", "extras.ddl_file" )
        infile = os.path.realpath( os.path.join( csvdir, dicfile ) )
        if not os.path.exists( infile ) :
            raise IOError( "File not found: %s" % (infile,) )
        with open( infile, "rU" ) as inf :
            lex = sas.StarLexer( inf, bufsize = 0, verbose = False ) #verbose )
            sas.DdlParser.parse( lexer = lex, content_handler = obj, error_handler = obj, verbose = False ) #verbose )

        if not obj._check() :
            sys.stderr.write( "********\n" )
            sys.stderr.write( "* ERROR: no rows in ddltypes\n" )
            sys.stderr.write( "********\n" )

        if connection is None :
            obj._db.close()

        return obj

    #
    #
    def __init__( self, *args, **kwargs ) :
        super( self.__class__, self ).__init__( *args, **kwargs )
        self._curs = None
        self._row = {}
        self._first_row = True
        self._in_loop = False

    #
    #
    def _check( self ) :
        rc = False
        if self._curs is None :
            self._curs = self._db.cursor()
        self._curs.execute( "select count(*) from ddltypes" )
        row = self._curs.next()

# there should be at least a few
#
        if int( row[0] ) > 5 :
            rc = True

        return rc

##########  SAS callbacks  ########################################################################

    def error( self, line, msg ) :
        sys.stderr.write( "parse error in line %d: %s\n" % (line,msg,) )
        if msg == "Loop count error" :
            if not self._in_loop : return False
        return True
    def comment( self, line, text ) : return False
    def startSaveframe( self, line, name ) : return False
    def endSaveframe( self, line, name ) : return False

    def startData( self, line, name ) :
        if self.verbose : sys.stdout.write( self.__class__.__name__ + ".startData(%s)\n" % (name,) )
        if self._curs is None :
            self._curs = self._db.cursor()
        self._curs.execute( "delete from ddltypes" )
        return False

    # commit and close -- __del__() is redundant
    #
    def endData( self, line, name ) :
        if isinstance( self._db, sqlite3.Connection ) :
            self._db.commit()
# need it for check
#            self._curs.close()

    #
    #
    def startLoop( self, line ) :
        self._first_row = True
        return False

    # commit last row
    #
    def endLoop( self, line ) :
        if self.verbose :
            sys.stdout.write( self.__class__.__name__ + ".endLoop()\n" )
            sys.stdout.write( self.SQL + "\n" )
            pprint.pprint( self._row )
        if len( self._row ) > 0 :
            self._curs.execute( self.SQL, self._row )
            self._row.clear()

# stop parsing after we've read the loop we're after
#
        if self._in_loop : 
            self._db.commit()
            return True
        return False

    #
    #
    def data( self, tag, tagline, val, valline, delim, inloop ) :
        if self.verbose : sys.stdout.write( self.__class__.__name__ + ".data()\n" )
        if not inloop : return False
        tag = tag.lower()
        if tag == "_item_type.code" :
            if not self._in_loop : self._in_loop = True
            if self._first_row :
                self._first_row = False
            else :
                if self._verbose :
                    sys.stdout.write( self.SQL + "\n" )
                    pprint.pprint( self._row )
                self._curs.execute( self.SQL, self._row )
                self._row.clear()

            if val is None :
                raise Exception( "NULL _item_type_list.code value in line %d" % (valline,) )

            self._row["type"] = str( val ).strip().replace( "\n", " " )
            return False

        if tag == "_item_type.construct" :
            if val is None :
                raise Exception( "NULL _item_type_list.construct value in line %d" % (valline,) )
            self._row["re"] = str( val ).strip().replace( "\n", " " )
            return False

        if tag == "_item_type.detail" :
            if val is not None :
                val = str( val ).strip().replace( "\n", " " )
                val = re.sub( r"\s+", " ", val )
            self._row["detail"] = val

        return False

####################################################################################################
#
if __name__ == "__main__" :

    props = ConfigParser.SafeConfigParser()
    props.read( sys.argv[1] )
    dbfile = props.get( "dictionary", "sqlite3.file" )
    if not os.path.exists( dbfile ) :
        raise IOError( "File not found: %s (create dictionary first?)" % (dbfile,) )
    db = DicParser.read_ddltypes( props, dburl = dbfile, verbose = True )
