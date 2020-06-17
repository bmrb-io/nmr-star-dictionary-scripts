#!/usr/bin/python -u
#
# extra_enumerations.str contains enumerations that are not in ADIT interface (lists too long) but
# are used for validation
#
# File format is sigle-column loops
#
#   save_<_Tag.Name>
#     loop_
#       _val
#       ...
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
class EnumerationParser( BaseClass, sas.ErrorHandler, sas.ContentHandler ) :

    """read extra_enumerations.str into sqlite3 dictionary database"""

    QRY = "select dictionaryseq from adit_item_tbl where originaltag=:tag"
    SQL = "insert into extra_enums (tagseq,val) values (:num,:val)"

    # main
    #
    @classmethod
    def read_enums( cls, props, connection = None, dburl = None, verbose = False ) :
        obj = cls( verbose = verbose )
        obj.config = props
        if connection is not None :
            obj.connection = connection
        else :
            obj.connect( url = dburl )
        csvdir = props.get( "dictionary", "csv.dir" )
        enumfile = props.get( "dictionary", "extras.enum_file" )
        infile = os.path.realpath( os.path.join( csvdir, enumfile ) )
        if not os.path.exists( infile ) :
            raise IOError( "File not found: %s" % (infile,) )
        with open( infile, "rU" ) as inf :
            lex = sas.StarLexer( inf, bufsize = 0, verbose = verbose )
            sas.SansParser.parse( lexer = lex, content_handler = obj, error_handler = obj, verbose = verbose )

        obj.check_dataset_categories()
        return obj

    #
    #
    def __init__( self, *args, **kwargs ) :
        super( self.__class__, self ).__init__( *args, **kwargs )
        self._curs = None
        self._last_seq = 0

#########  SAS callbacks  #########################################################################
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

    # commit and close
    #
    def endData( self, line, name ) :
        self._db.commit()
        self._curs.close()

# need database open for the checker method
#        self._db.close()

    # look up tag sequence number
    #
    def startSaveframe( self, line, name ) :
        if self._verbose : sys.stdout.write( self.__class__.__name__ + ".startSaveframe(%s)\n" % (name,) )
        self._curs.execute( self.QRY, { "tag" : name } )
        row = self._curs.fetchone()
        if row is None :
            sys.stderr.write( "No sequence number for tag %s\n" % (name,) )
            return True
        self._last_seq = row[0]
        return False

    #
    #
    def endSaveframe( self, line, name ) :
        self._last_seq = 0
        return False

    # just commit every tag since it's a loop w/ 1 column
    #
    def data( self, tag, tagline, val, valline, delim, inloop ) :
        if tag == "_item_enumeration.value" :
            params = { "num" : self._last_seq }
            if val is not None :
                val = str( val ).strip()
                if val in ( "", ".", "?" ) :
                    val = None
            if val is not None :
                params["val"] = val
                self._curs.execute( self.SQL, params )
        return False

    # enumeration for _Data_set.Type should match saveframe categories
    #
    def check_dataset_categories( self ) :
        if self._verbose : sys.stdout.write( self.__class__.__name__ + ".check_dataset_categories()\n" )
        sql = "select distinct sfcategory from cat_grp"
        cats = []
        curs = self._db.cursor()
        curs.execute( sql )
        while( True ) :
            row = curs.fetchone()
            if row is None : break
            cats.append( row[0] )

        sql = "select val from val_enums v join val_item_tbl a on a.dictionaryseq=v.tagseq " \
            + "where a.originaltag='_Data_set.Type'"
        curs.execute( sql )
        while( True ) :
            row = curs.fetchone()
            if row is None : break
            if not row[0] in cats :
                sys.stderr.write( "Data_set.Type value %s not a saveframe category" % (row[0],) )
        curs.close()

####################################################################################################
#
if __name__ == "__main__" :

    props = ConfigParser.SafeConfigParser()
    props.read( sys.argv[1] )
    dbfile = props.get( "dictionary", "sqlite3.file" )
    if not os.path.exists( dbfile ) :
        raise IOError( "File not found: %s (create dictionary first?)" % (dbfile,) )
    db = EnumerationParser.read_enums( props, dburl = dbfile, verbose = False )
