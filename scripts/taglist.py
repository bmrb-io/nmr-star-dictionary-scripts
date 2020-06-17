#!/usr/bin/python -u
#
#

"""NMR-STAR 3 dictionary sqlite3 database"""

from __future__ import absolute_import

import sys
import os
import sqlite3
import ConfigParser
import pprint
import re
import csv


if __package__ is None :
    __package__ = "nmr-star-dictionary-scripts"
    sys.path.append( os.path.abspath( os.path.join( os.path.split( __file__ )[0], ".." ) ) )
    from scripts import sas as sas
    from scripts import BaseClass as BaseClass
else :
    from . import sas
    from . import BaseClass

class QuickValidate( BaseClass ) :

    """creates a list of valid NMR-STAR tags"""

    # main
    #
    @classmethod
    def create_taglist( cls, props, dburl = None, outfile = None, verbose = False ) :
        obj = cls( verbose = verbose )
        obj.config = props
        obj.connect( url = dburl )
        if outfile is None : 
            obj.list_tags( out = sys.stdout )
        else :
            with open( outfile, "wb" ) as out :
                obj.list_tags( out = out )

        return obj

    #
    #
    def __init__( self, *args, **kwargs ) :
        super( self.__class__, self ).__init__( *args, **kwargs )

    #
    #
    def list_tags( self, out = None ) :
        if self.verbose : sys.stdout.write( self.__class__.__name__ + ".list_tags()\n" )

# 20170921 - Eldon's dictionary flags are messed up or something so this needs manual massaging
#

        tags = set()
        curs = self._db.cursor()
#        sql = "select i.originaltag,i.internalflag,p.printflag from adit_item_tbl i" \
        sql = "select i.originaltag from adit_item_tbl i" \
            + " join validator_printflags p on p.dictionaryseq=i.dictionaryseq" \
            + " where (i.internalflag is null or i.internalflag=='N')" \
            + " and (not p.printflag=='N')" \
            + " order by i.dictionaryseq"
        curs.execute( sql )
        while True :
            row = curs.fetchone()
            if row == None : break
            tags.add( str( row[0] ).strip() )
        curs.close()

        for i in ( 
"_Entity_natural_src.Subvariant",
"_Entity_natural_src.Cellular_location",
"_Entity_natural_src.Fragment",
"_Entity_natural_src.Fraction",
"_Entity_natural_src.Plasmid_details",
"_Entity_natural_src.Dev_stage",
"_Entity_natural_src.Citation_ID",
"_Entity_natural_src.Citation_label",
"_Entity_experimental_src.Host_org_subvariant",
"_Entity_experimental_src.Host_org_organ",
"_Entity_experimental_src.Host_org_tissue",
"_Entity_experimental_src.Host_org_tissue_fraction",
"_Entity_experimental_src.Host_org_cell_line",
"_Entity_experimental_src.Host_org_cell_type",
"_Entity_experimental_src.Host_org_cellular_location",
"_Entity_experimental_src.Host_org_organelle",
"_Entity_experimental_src.Host_org_gene",
"_Entity_experimental_src.Host_org_culture_collection",
"_Entity_experimental_src.Host_org_dev_stage",
"_Entity_experimental_src.Citation_ID",
"_Entity_experimental_src.Citation_label",
"_Chem_shift_ref.Indirect_shift_ratio_cit_ID",
"_Chem_shift_ref.Indirect_shift_ratio_cit_label",
"_Chem_shift_ref.Correction_val_cit_ID",
"_Chem_shift_ref.Correction_val_cit_label",
"_Chem_shift_ref.Indirect_shift_ratio_cit_ID",
"_Chem_shift_ref.Indirect_shift_ratio_cit_label",
"_Chem_shift_ref.Correction_val_cit_ID",
"_Chem_shift_ref.Correction_val_cit_label",
"_Chem_shift_ref.Indirect_shift_ratio_cit_ID",
"_Chem_shift_ref.Indirect_shift_ratio_cit_label",
"_Chem_shift_ref.Correction_val_cit_ID",
"_Chem_shift_ref.Correction_val_cit_label") :
            tags.add( i )

        for i in tags :
            out.write( '"%s"\n' % (i,) )


####################################################################################################
#
if __name__ == "__main__" :

    props = ConfigParser.SafeConfigParser()
    props.read( sys.argv[1] )
    dbfile = props.get( "dictionary", "sqlite3.file" )
    db = QuickValidate.create_taglist( props, verbose = False )

