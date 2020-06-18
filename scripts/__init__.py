#!/usr/bin/python -u
#

import sys
import sqlite3
import ConfigParser
import re

try : 
    LIB_PATH = "/bmrb/lib/python27"
    sys.path.append( LIB_PATH )
    import sas
except ImportError :
    import sas

# quote string for STAR
#
def quote4star( instr ) :
    if instr is None : return "."
    val = str( instr )
    if val == "" : return "."
    dq1 = re.compile( "\s+\"" )
    dq2 = re.compile( "\"\s+" )
    sq1 = re.compile( "\s+'" )
    sq2 = re.compile( "'\s+" )
    spc = re.compile( "\s+" )
    usc = re.compile( "^_" )
    dat = re.compile( "^data_[^\s]", re.IGNORECASE )
    sav = re.compile( "^save_", re.IGNORECASE )
    lop = re.compile( "^loop_\s*$", re.IGNORECASE )
    stp = re.compile( "^stop_\s*$", re.IGNORECASE )
    if "\n" in val :
        if val.endswith( "\n" ) : return ";\n" + val + ";"
        else : return ";\n" + val + "\n;"

    has_dq = False
    m = dq1.search( val )
    if m : has_dq = True
    else :
        m = dq2.search( val )
        if m : has_dq = True
    has_sq = False
    m = sq1.search( val )
    if m : has_sq = True
    else :
        m = sq2.search( val )
        if m : has_sq = True
    if has_sq and has_dq : return ";\n" + val + "\n;"
    val = val.strip()
    if has_sq : return "\"" + val + "\""
    if has_dq : return "'" + val + "'"
    m = spc.search( val )
    if m : return "'" + val + "'"
    m = usc.search( val )
    if m : return "'" + val + "'"
    m = dat.search( val )
    if m : return "'" + val + "'"
    m = sav.search( val )
    if m : return "'" + val + "'"
    m = lop.search( val )
    if m : return "'" + val + "'"
    m = stp.search( val )
    if m : return "'" + val + "'"
    return val

# common stuff: db connection, config obj and verbose flag
#
class BaseClass( object ) :
    #
    #
    def __init__( self, verbose = False ) :
        if verbose : sys.stdout.write( self.__class__.__name__ + ".__init__()\n" )
        self._verbose = bool( verbose )
        self._props = None
        self._db = None

    #
    #
    def __del__( self ) :
        try :
            if isinstance( self._db, sqlite3.Connection ) :
                try :
                    self._db.commit()
                    self._db.close()
                except sqlite3.ProgrammingError :

# already closed presumably?
#
                    pass

# _db not there? (how TF does that happen)
#
        except AttributeError :
            pass

    #
    #
    @property
    def verbose( self ) :
        """verbose flag"""
        return bool( self._verbose )
    @verbose.setter
    def verbose( self, flag ) :
        self._verbose = bool( flag )

    #
    #
    @property
    def config( self ) :
        """configparser object"""
        return self._props
    @config.setter
    def config( self, config ) :
        assert isinstance( config, ConfigParser.SafeConfigParser )
        self._props = config

    #
    #
    @property
    def connection( self ) :
        """sqlite3 db connection"""
        return self._db
    @connection.setter
    def connection( self, conn ) :
        assert isinstance( conn, sqlite3.Connection )
        self._db = conn
    def connect( self, url ) :
        if url is None :
            assert isinstance( self._props, ConfigParser.SafeConfigParser )
            url = self._props.get( "dictionary", "sqlite3.file" )
        self._db = sqlite3.connect( url )

####################################################################################################

from .dictdb import DictDB
from .aditifdic import DicParser as DicParse
from .comments import CommentParser as CommentParse
from .internaldic import DicParser as DdlParse
from .enumerations import EnumerationParser as EnumParse
from .definitions import TagdefReader as DefParse
from .validict import ValidatorDictionary
from .aditout import AditWriter
from .csvout import CsvWriter
from .validator import ValidatorWriter
from .taglist import QuickValidate

__all__ = [ "sas",
            "BaseClass", "quote4star",
            "DictDB", "DicParse", "CommentParse", "DdlParse", "EnumParse", "DefParse",
            "ValidatorDictionary", "AditWriter", "CsvWriter", "ValidatorWriter",
            "QuickValidate" ]
