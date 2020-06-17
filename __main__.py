#!/usr/bin/python -u
#
# create NMR-STAR dictionary files
#
#
from __future__ import absolute_import

import sys
import os
import argparse
import ConfigParser

# from .
import scripts

if __name__ == "__main__" :

    ap = argparse.ArgumentParser( description = "Process NMR-STAR dictionary" )
    ap.add_argument( "-c", "--config", help = "config file", dest = "conffile", required = True )
    ap.add_argument( "-v", "--verbose", help = "print lots of messages to stdout", dest = "verbose",
        action = "store_true", default = False )
    args = ap.parse_args()

# read it in
#
    props = ConfigParser.SafeConfigParser()
    props.read( args.conffile )

    dbfile = props.get( "dictionary", "sqlite3.file" )
    if os.path.exists( dbfile ) :
        os.unlink( dbfile )

    db = scripts.DictDB.create_dictionary( props, verbose = args.verbose )
    if len( db._errors ) > 0 :
        for e in db._errors :
            sys.stderr.write( e + "\n" )

# some of them are warnings, actually
#        sys.exit( 1 )
# 20191220 don't need adit
#    sys.stdout.write( ">> read_descriptions\n" )
#    scripts.DicParse.read_descriptions( props, dburl = dbfile, verbose = args.verbose )
    sys.stdout.write( ">> read_comments\n" )
    scripts.CommentParse.read_comments( props, dburl = dbfile, verbose = args.verbose )
    sys.stdout.write( ">> read_ddltypes\n" )
    scripts.DdlParse.read_ddltypes( props, dburl = dbfile, verbose = True ) # args.verbose )
    sys.stdout.write( ">> read_enums\n" )
    scripts.EnumParse.read_enums( props, dburl = dbfile, verbose = args.verbose )
    sys.stdout.write( ">> read_definition\n" )
    scripts.DefParse.read_definitions( props, dburl = dbfile, verbose = args.verbose )
    sys.stdout.write( ">> make_validator_tables\n" )
    scripts.ValidatorDictionary.make_validator_tables( props, dburl = dbfile, verbose = args.verbose )

# make ADIT-NMR files
#
#    scripts.AditWriter.make_adit_files( props, dburl = dbfile, verbose = args.verbose )

# make website db files
#
    scripts.CsvWriter.make_output_files( props, dburl = dbfile, verbose = args.verbose )

# and validation dictionary for the annotators/ADIT-NMR post-processor
#
    scripts.ValidatorWriter.create_validator_dictionary( props, dburl = dbfile, verbose = args.verbose )

# and taglist file for "quickcheck" validaton when copying files to public website
#
    listfile = props.get( "dictionary", "taglist.file" )
    scripts.QuickValidate.create_taglist( props, dburl = dbfile, outfile = listfile, verbose = args.verbose )
