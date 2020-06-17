#!/usr/bin/python -u
#
# comments.str contains boilerplate comments inserted into released entries
#

from __future__ import absolute_import

import sys
import os
import sqlite3
import ConfigParser

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
class CommentParser( BaseClass, sas.ErrorHandler, sas.ContentHandler ) :

    """read comments.str into sqlite3 dictionary database"""

    SQL = "insert into comments (comment,everyflag,sfcategory,tagname) values (:comment,:every," \
        + ":sfcat,:tag)"

    # main
    #
    @classmethod
    def read_comments( cls, props, connection = None, dburl = None, verbose = False ) :
        obj = cls( verbose = verbose )
        obj.config = props
        if connection is not None :
            obj.connection = connection
        else :
            obj.connect( url = dburl )
        csvdir = props.get( "dictionary", "csv.dir" )
        comfile = props.get( "dictionary", "extras.comment_file" )
        infile = os.path.realpath( os.path.join( csvdir, comfile ) )
        if not os.path.exists( infile ) :
            raise IOError( "File not found: %s" % (infile,) )
        with open( infile, "rU" ) as inf :
            lex = sas.StarLexer( inf, bufsize = 0, verbose = verbose )
            sas.SansParser.parse( lexer = lex, content_handler = obj, error_handler = obj, verbose = verbose )
        return obj

    #
    #
    def __init__( self, *args, **kwargs ) :
        super( self.__class__, self ).__init__( *args, **kwargs )
        self._row = {}
        self._curs = None
        self._first_row = True

#########  SAS callbacks  #########################################################################
    def error( self, line, msg ) :
        sys.stderr.write( "parse error in line %d: %s\n" % (line,msg,) )
        return True
    def comment( self, line, text ) : return False
    def startSaveframe( self, line, name ) : return False
    def endSaveframe( self, line, name ) : return False

    def startData( self, line, name ) :
        if self._verbose : sys.stdout.write( self.__class__.__name__ + ".startData(%s)\n" % (name,) )
        if self._curs is None :
            self._curs = self._db.cursor()

# clean up first
#
        self._curs.execute( "delete from comments" )
        return False

    # commit and close -- __del__() is redundant
    #
    def endData( self, line, name ) :
        if isinstance( self._db, sqlite3.Connection ) :
            self._db.commit()
            self._curs.close()
            self._db.close()

    #
    #
    def startLoop( self, line ) :
        self._first_row = True
        return False

    # insert last row
    #
    def endLoop( self, line ) :
        if self._verbose : sys.stdout.write( self.__class__.__name__ + ".endLoop()\n" )
        self._curs.execute( self.SQL, self._row )
        if self._verbose : sys.stdout.write( ">>> %d rows inserted\n" % (self._curs.rowcount,) )
        return False

    #
    #
    def data( self, tag, tagline, val, valline, delim, inloop ) :
        if self._verbose : sys.stdout.write( self.__class__.__name__ + ".data()\n" )
        if not inloop : return False

# _comment is the 1st tag in the loop. commit the previous row unless it's the very first one.
#
        if tag == "_comment" :
            if self._first_row :
                self._first_row = False
            else :
                self._curs.execute( self.SQL, self._row )
                if self._verbose : sys.stdout.write( ">>> %d rows inserted\n" % (self._curs.rowcount,) )

            self._row.clear()
            self._row["comment"] = val
            return False

        if tag == "_every_flag" :
            if (val is not None) and (val.strip().upper() == 'Y') :
                self._row["every"] = "true"
            else :
                self._row["every"] = "false"
            return False

        if tag == "_category" :
            if val is None : raise Exception( "Empty value for %s in line %d" % (tag,valline,) )
            self._row["sfcat"] = str( val ).strip()
            return False

        if tag == "_tagname" :
            if val is None :
                self._row["tag"] = None
            elif str( val ).strip() == "." :
                self._row["tag"] = None
            else :
                self._row["tag"] = str( val ).strip()

        return False

####################################################################################################
#
if __name__ == "__main__" :

    props = ConfigParser.SafeConfigParser()
    props.read( sys.argv[1] )
    dbfile = props.get( "dictionary", "sqlite3.file" )
    if not os.path.exists( dbfile ) :
        raise IOError( "File not found: %s (create dictionary first?)" % (dbfile,) )
    db = CommentParser.read_comments( props, dburl = dbfile, verbose = False )
