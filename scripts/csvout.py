#!/usr/bin/python -u
#
# dump dictionary tables to CSV
#
# this is used by the website: both lookup interface and for creating the databases
#
from __future__ import absolute_import

import sys
import os
import sqlite3
import ConfigParser

if __package__ is None :
    __package__ = "nmr-star-dictionary-scripts"
    sys.path.append( os.path.abspath( os.path.join( os.path.split( __file__ )[0], ".." ) ) )
    from scripts import BaseClass as BaseClass
else :
    from . import BaseClass

# just a wrapper for a very straightforward csv dump
#
class CsvWriter( BaseClass ) :

    TABLES = [ "adit_item_tbl", "aditenumhdr", "aditenumdtl", "aditcatgrp", "aditsupergrp", 
        "aditenumtie", "aditmanoverride", "nmrcifmatch", "validationlinks", "validationoverrides",
        "ddltypes", "comments", "extra_enums", "query_interface", "validator_printflags", 
        "validator_sfcats" ]

    # main
    #
    @classmethod
    def make_output_files( cls, props, connection = None, dburl = None, verbose = False ) :
        obj = cls( verbose = verbose )
        obj.config = props
        outdir = os.path.realpath( props.get( "www", "output_dir" ) )
        if not os.path.isdir( outdir ) :
            os.makedirs( outdir )
        if connection is None :
            obj.connect( url = dburl )
        else :
            obj.connection = connection
        obj.outdir = outdir
        obj.dump_csv()
        obj.make_sql_script()

        return obj

    #
    #
    def __init__( self, *args, **kwargs ) :
        super( self.__class__, self ).__init__( *args, **kwargs )
        self._outdir = None

    #
    #
    @property
    def outdir( self ) :
        """output directory"""
        return self._outdir
    @outdir.setter
    def outdir( self, path ) :
        d = os.path.realpath( path )
        assert os.path.isdir( d )
        self._outdir = d

    #
    #
    def dump_csv( self ) :
        curs = self._db.cursor()
        for table in self.TABLES :
            sql = "select count(*) from %s" % (table)
            curs.execute( sql )
            row = curs.fetchone()
            if (row is None) or (row[0] < 1) : continue

            sql = "select * from %s" % (table)
            curs.execute( sql )

# rename back to what Eldon originally called it
#
            if table == "dict" :
                outfile = os.path.join( self._outdir, "dict.val_item_tbl.csv" )
            else :
                outfile = os.path.join( self._outdir, ("dict.%s.csv" % (table,)) )

            with open( outfile, "w" ) as out :
                for i in range( len( curs.description ) ) :
                    out.write( "\"%s\"" % curs.description[i][0].lower() )
                    if i < (len( curs.description ) - 1) : 
                        out.write( "," )
                out.write( "\n" )

                while True :
                    row = curs.fetchone()
                    if row is None : break
                    for i in range( len( curs.description ) ) :
                        if row[i] is not None :
                            try : 
                                f = float( row[i] )
                                out.write( "%s" % (str( row[i] ).strip()) )
                            except ValueError :

# spec. case: true/false to yes/no
#
                                if (table == "comments") and (curs.description[i][0] == "everyflag") :
                                    if row[i] == "false" : out.write( "\"N\"" )
                                    else : out.write( "\"Y\"" )
                                else : 
                                    out.write( "\"%s\"" % (row[i].strip().replace( "\"", "\"\"" )) )
                        if i < (len( row ) - 1) : out.write( "," )
                    out.write( "\n" )

        curs.close()

    # DDL script for the above is split into several SQL scripts. cat them together in order
    #
    def make_sql_script( self ) :
        sqldir = os.path.realpath( self._props.get( "www", "sql_dir" ) )
        outfile = os.path.realpath( os.path.join( self._outdir, self._props.get( "www", "scriptfile" ) ) )
        infiles = self._props.get( "www", "sql_files" ).split()
        with open( outfile, "w" ) as out :
            for infile in infiles :
                with open( os.path.realpath( os.path.join( sqldir, infile.strip() ) ), "r" ) as fin :
                    for line in fin :
                        out.write( line )

####################################################################################################
#
if __name__ == "__main__" :

    props = ConfigParser.SafeConfigParser()
    props.read( sys.argv[1] )
    dbfile = props.get( "dictionary", "sqlite3.file" )
    if not os.path.exists( dbfile ) :
        raise IOError( "File not found: %s (create dictionary first?)" % (dbfile,) )
    db = CsvWriter.make_output_files( props, dburl = dbfile, verbose = False )
