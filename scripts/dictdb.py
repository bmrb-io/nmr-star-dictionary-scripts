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

class DictDB( BaseClass ) :

    """sqlite3 database wrapper"""

    # main
    #
    @classmethod
    def create_dictionary( cls, props, dburl = None, verbose = False ) :
        obj = cls( verbose = verbose )
        obj.config = props
        obj.connect( url = dburl )
        obj.create_tables()
        obj.load_tables()
        obj.fixup()
        obj.fix_query_interface()
        obj.check_labels()
        obj.check_framecodes()
        obj.check_internalflag()
        obj.check_tables()
        obj.check_sql_keywords()

        return obj

    #
    #
    def __init__( self, *args, **kwargs ) :
        super( self.__class__, self ).__init__( *args, **kwargs )
        self._errors = []

    #
    #
    def create_tables( self ) :
        if self.verbose : sys.stdout.write( self.__class__.__name__ + ".create_tables()\n" )

        scriptfile = self._props.get( "dictionary", "sql.table_script" )
        if not os.path.exists( scriptfile ) :
            raise IOError( "file not found: " + scriptfile )

        try :
            curs = self._db.cursor()
            with open( scriptfile, "rb" ) as fin :
                script = "".join( line for line in fin )
            if self.verbose : sys.stdout.write( script + "\n" )
            curs.executescript( script )

            curs.close()
        except sqlite3.OperationalError :
# print offending stetement?
            raise

    #
    #
    def load_table( self, section_name ) :
        if self.verbose : sys.stdout.write( self.__class__.__name__ + ".load_table(%s)\n" % (section_name,) )

        csvdir = self._props.get( "dictionary", "csv.dir" )
        if not os.path.isdir( csvdir ) :
            raise IOError( "directory not found: " + csvdir )

        db_table_name = self._props.get( section_name, "name" )
        csv_file_name = self._props.get( section_name, "csv.file" )
        numcols = self._props.getint( section_name, "numcols" )

        sql = "insert into " + db_table_name + "("
        for i in range( numcols ) :
            key = "col" + str( i )
            sql += self._props.get( section_name, key )
            if i < (numcols - 1) : sql += ","

        sql += ") values ("
        for i in range( numcols ) :
            sql += "?,"
        sql = sql[:-1]
        sql += ")"
        if self.verbose : sys.stdout.write( sql + "\n" )

# Eldon's input has to be cleaned up. in particular, he uses '$' for commas as excel's csv output
# doesn't quote string values
#
        vals = []
        with self._db :
            curs = self._db.cursor()
            with open( os.path.join( csvdir, csv_file_name ), "rU" ) as fin :
                rdr = csv.reader( fin )
                in_data = False
                for row in rdr :
                    if self.verbose : pprint.pprint( row )

                    if not in_data :
                        if row[0] == "TBL_BEGIN" :
                            in_data = True
                            continue
                        else : continue
                    else :
                        if row[0] == "TBL_END" :
                            in_data = False
                            continue

                    del vals[:]
                    for i in range( len( row ) ) :
                        if row[i] is None : 
                            vals.append( None )
                            continue

                        val = row[i].strip()
                        if (val is None) or (len( val ) < 1) : 
                            vals.append( None )
                            continue

# strip quotes if any
#
                        if val[0] in ( "'", "\"" ) :
                            val = val.strip( "'" )
                            val = val.strip( "\"" )
                            val = val.strip()

                        if (val is None) or (len( val ) < 1) :
                            vals.append( None )
                            continue

                        if not all( ord( c ) < 128 for c in val ) :
                            sys.stderr.write( "Non-ascii character in %s in %s\n" % (val, csv_file_name) )
                            self._errors.append( "Non-ascii character in %s in %s\n" % (val, csv_file_name) )
#                            vals.append( unicodedata.normalize( 'NFKD', val.decode( 'utf-8' ).encode( 'ascii', 'ignore' ) ) )
                            vals.append( "BORKBORKBORK" )
                            continue

# Eldon's sure there's no legitimate '$' anywhere
#
                        val = val.replace( "$", "," )

# "?" is a valid enum value
#
                        if (val == ".") or (val == "?") :
                            if db_table_name == "aditenumdtl" :
                                vals.append( val )
                            else :
                                vals.append( None )
                        else :
                            vals.append( val )

                    if self.verbose : pprint.pprint( vals )
                    curs.execute( sql, tuple( vals ) )
                    if self.verbose : sys.stdout.write( "- %d\n" % (curs.rowcount,) )

            curs.close()

    # load all tables listed in .props
    #
    def load_tables( self ) :
        if self.verbose : sys.stdout.write( self.__class__.__name__ + ".load_tables()\n" )

        namepat = re.compile( r"^table_\d+$" )
        for s in sorted( self._props.sections() ) :
            m = namepat.search( s )
            if m :
                self.load_table( section_name = s )

    # misc. post-cook fixes
    #
    def fixup( self ) :
        if self.verbose : sys.stdout.write( self.__class__.__name__ + ".fixup()\n" )

# entry completeness rules: table level
# - if last validateflg on a primary key tag is R, then the table is required
# - "proper" requirements are in aditcatgrp
#
# the latter allow for "and" and "or" i.e. saveframe foo must have tables X and Y
#
        got = []
        add = {}
        with self._db :
            curs = self._db.cursor()

#20180301 TEMP: this tag's a left-over from NEF stuff, will be removed upstram in a future update
#
            sql = "delete from adit_item_tbl where originaltag='_Peak.Index_ID'"
            curs.execute( sql )
            if self.verbose :
                sys.stdout.write( "* %s: %d rows\n" % (sql,curs.rowcount) )

#
            sql = "select distinct sfcategory from aditcatgrp where mandatorytagcats is not null"
            curs.execute( sql )
            while True :
                row = curs.fetchone()
                if row is None : break
                got.append( row[0] )
            if self.verbose :
                sys.stdout.write( "* got:\n" )
                pprint.pprint( got )

            sql = "select distinct originalcategory,tagcategory from adit_item_tbl " \
                + "where primarykey='Y' and loopflag='Y' and validateflgs like '%R' " \
                + "order by originalcategory,tagcategory"
            curs.execute( sql )
            while True :
                row = curs.fetchone()
                if row is None : break
                if row[0] in got : continue  # new rules override old rules
                if not row[0] in add.keys() :
                    add[row[0]] = None
                if add[row[0]] is None : add[row[0]] = row[1]
                else : add[row[0]] = "%s and %s" % (add[row[0]],row[1])
            if self.verbose :
                sys.stdout.write( "* add:\n" )
                pprint.pprint( add )

            if len( add ) > 0 :
                sql = "update aditcatgrp set mandatorytagcats=? where sfcategory=? and mandatorytagcats is null" # tobesure
                for (sfcat,tagcats) in add.items() :
                    if self._verbose : sys.stdout.write( sql.replace( "?", "%s" ) % (tagcats,sfcat) )
                    curs.execute( sql, (tagcats,sfcat) )
                    if self._verbose : sys.stdout.write( ": %d\n" % (curs.rowcount,) )

#
#
            curs.close()

    # check/fix query inteface in case sequence numbers are fscked
    #
    def fix_query_interface( self ) :
        if self.verbose : sys.stdout.write( self.__class__.__name__ + ".fix_query_interface()\n" )

        with self._db :
            rows = []
            curs = self._db.cursor()

            sql = "update query_interface set dictionaryseq=" \
                + "(select dictionaryseq from adit_item_tbl " \
                + "where tagcategory=query_interface.tagcategory " \
                + "and tagfield=query_interface.tagfield)"
            curs.execute( sql )
            if self.verbose :
                sys.stdout.write( "* %s: %d rows\n" % (sql,curs.rowcount) )

            print_header = True
            sql = "select a.dictionaryseq,b.dictionaryseq,a.tagcategory,a.tagfield " \
                + "from adit_item_tbl a join query_interface b " \
                + "on b.tagcategory=a.tagcategory and b.tagfield=a.tagfield " \
                + "where a.dictionaryseq<>b.dictionaryseq " \
                + "order by a.dictionaryseq"
            curs.execute( sql )
            while True :
                row = curs.fetchone()
                if row is None : break
                if print_header :
                    self._errors.append( "Bad tag sequence numbers in query interface table" )
                    sys.stderr.write( "!!! query interface tags with bad sequence numbers\n" )
                    print_header = False
                sys.stderr.write( "%s,%s,%s,%s\n" % tuple( row ) )
            curs.close()

#
# The rules:
#  .Sf_framecode tags have bmrbtype framecode and sfnameflg = Y
#  _label tags have bmrbtype framecode, sfnameflg = N, and sfpointerflg = Y
#
#
# Go through tags that have "_label" in the name, check that
# 1. bmrbtype is "label"
# 2. framecodevalueflg is 'Y'
# 3. it has a foreign key
# 4. there is a coresp. "_ID" tag
# 5.   and it has a foreign key
#
# Look for ones with bmrbtype label that aren't labels
#
    def check_labels( self ) :
        if self.verbose : sys.stdout.write( self.__class__.__name__ + "._check_labels()\n" )

        pat = re.compile( r"(_.+\..+)_label(_.+)*" )
        curs1 = self._db.cursor()
        curs2 = self._db.cursor()
        sql = "select foreigncolumn,foreigntable,aditautoinsert from adit_item_tbl " \
            + "where originaltag=?"
        qry = "select originaltag,sfpointerflg,foreigncolumn,foreigntable,aditautoinsert," \
            + "bmrbtype,dictionaryseq from adit_item_tbl order by dictionaryseq"
        curs1.execute( qry )
        while True :
            row = curs1.fetchone()
            if row is None : break

            fcode = False
            fkey = None
            idtag = None

# there's a couple fo tags with "_label" in the name that aren't framecodes
#  are there framecodes without "_label"?
#
            m = pat.search( row[0] )
            if (row[1] is not None) and (str( row[1] ).strip().lower()[0:1] == 'y') :
                fcode = True
                if not m :
                    self._errors.append( "%s: framecode tag (sfPointerFlg='Y') without '_label' in the name" % (row[0],) )
                    if row[5] != "framecode" : 
                        self._errors.append( "%s: bmrbtype is not framecode: %s" % (row[0],row[5],) )
                    continue

            if not m :
                continue

            if not fcode :
                self._errors.append( "%s: sfPointerFlg is not 'Y'" % (row[0],) )
                continue

# these are framecodes with "_label"
#
            if row[5] != "framecode" : 
                self._errors.append( "%s: bmrbtype is not framecode: %s" % (row[0],row[5],) )
            if (row[2] is not None) and (row[3] is not None) :
                fkey = "_" + str( row[3] ) + "." + str( row[2] )
            if fkey is None : 
                self._errors.append( "%s: no foreign key" % (row[0],) )

            idtag = m.group( 1 ) + "_ID"
            if m.group( 2 ) is not None : idtag += m.group( 2 )
            if idtag is None :
                self._errors.append( "%s: no matching id tag %s (this can never happen)" % (row[0],idtag,) )
                continue

            curs2.execute( sql, (idtag,) )
            idrow = curs2.fetchone()
            if idrow is None :
                self._errors.append( "%s: no matching ID tag %s" % (row[0],idtag,) )
            else :
                if (idrow[0] is None) or (idrow[1] is None) :
                    self._errors.append( "%s: ID tag has no foreign key" % (idtag,) )

        curs2.close()
        curs1.close()


# 1. go through all tags that have Sf_framecode in the name, check that 
#   their bmrbtype is framecode
#   sfNameFlg is Y
# 2. go through all tags whose sfNameFlg is Y, check that
#   bmrbtype is framecode
#   Sf_framecode is in the name
#
    def check_framecodes( self ) :
        if self.verbose : sys.stdout.write( self.__class__.__name__ + "._check_framecodes()\n" )

        curs = self._db.cursor()
        sql = "select originaltag,sfnameflg,bmrbtype,dictionaryseq from adit_item_tbl " \
            + "where tagfield='Sf_framecode' order by dictionaryseq"
        curs.execute( sql )
        while True :
            row = curs.fetchone()
            if row is None : break

            if (row[1] is None) or (str( row[1] ).strip().lower()[0:1] != 'y') :
                self._errors.append( "%s : sfNameFlg is not 'Y'" % (row[0],) )

            if (row[2] is None) or (str( row[2] ).strip().lower() != 'framecode') :
                self._errors.append( "%s : bmrbtype is not 'framecode'" % (row[0],) )

        fcpat = re.compile( "^Sf_framecode$" )
        sql = "select originaltag,tagfield,bmrbtype,dictionaryseq from adit_item_tbl " \
            + "where sfnameflg='Y' or sfnameflg='y' order by dictionaryseq"
        curs.execute( sql )
        while True :
            row = curs.fetchone()
            if row is None : break

            m = fcpat.search( row[1] )
            if not m :
                self._errors.append( "%s : sfNameFlg is 'Y', name is not .Sf_framecode" % (row[0],) )

            if (row[2] is None) or (str( row[2] ).strip().lower() != 'framecode') :
                self._errors.append( "%s : sfNameFlg is 'Y', bmrbtype is not framecode" % (row[0],) )

        curs.close()

####################################################################################################
# compare "non-public" with validate flag in column 0
# should be 'Y' <= 'I'
#
    def check_internalflag( self ) :
        if self.verbose : sys.stdout.write( self.__class__.__name__ + "._check_internalflag()\n" )

        sql = "select originaltag,internalflag,validateflgs,dictionaryseq from adit_item_tbl " \
            + "where validateflgs like '%I%' order by dictionaryseq"
        curs = self._db.cursor()
        curs.execute( sql )
        while True :
            row = curs.fetchone()
            if row is None : break
            if str( row[2] ).strip().upper()[0] == "I" :
                if (row[1] is None) or (str( row[1] ).strip().upper() != "Y") :
                    self._errors.append( "%s : validateflgs[0] is %s, internalflag is %s" % (row[0],row[2],row[1]) )

        sql = "select originaltag,internalflag,validateflgs,dictionaryseq from adit_item_tbl " \
            + "where internalflag='Y' order by dictionaryseq"
        curs = self._db.cursor()
        curs.execute( sql )
        while True :
            row = curs.fetchone()
            if row is None : break
            if str( row[2] ).strip().upper()[0] != "I" :
                self._errors.append( "%s : internalflag='Y', validateflgs[0] is %s" % (row[0],row[2]) )

        curs.close()

# see that all free tables have Sf_framecode and Sf_category,
# all tables have Sf_ID and local id "local sf id".
# all tags in a table must have the same "metadata flag": 'Y' or 'N'
#
# "local sf id" is something that ADIT-NMR uses in some places to fake out saveframes
# in its internal saveframeless "nmrif" format. (it uses local ids in some other places
# and regular sf ids in other other places...)
#
    def check_tables( self ) :
        if self.verbose : sys.stdout.write( self.__class__.__name__ + "._check_tables()\n" )

        tables = []
        sql = "select distinct tagcategory,min(dictionaryseq) from adit_item_tbl where loopflag='N' " \
            + "group by tagcategory order by min(dictionaryseq)"
        curs = self._db.cursor()
        curs.execute( sql )
        while True :
            row = curs.fetchone()
            if row is None : break
            tables.append( row[0] )

        sql = "select count(*) from adit_item_tbl where tagcategory=? and tagfield=?"
        freetags = ("Sf_category", "Sf_framecode","ID")
        for table in tables :
            for column in freetags :
                curs.execute( sql, (table, column) )
                row = curs.fetchone()
                if int( row[0] ) != 1 :
                    self._errors.append( "Free table %s has %d %s tags" % (table, int( row[0] ), column) )

        del tables[:]
        sql = "select distinct tagcategory,min(dictionaryseq) from adit_item_tbl " \
            + "group by tagcategory order by min(dictionaryseq)"
        curs.execute( sql )
        while True :
            row = curs.fetchone()
            if row is None : break
            tables.append( row[0] )

# check by tag name
#
        sql = "select count(*) from adit_item_tbl where tagcategory=? and tagfield=?"
        alltags = ("Sf_ID", "Entry_ID")
        for table in tables :
            for column in alltags :
                curs.execute( sql, (table, column) )
                row = curs.fetchone()
                if int( row[0] ) != 1 :
                    if (table == "Entry") and (column == "Entry_ID") :
                        continue
                    self._errors.append( "Table %s has %d %s tags" % (table, int( row[0] ), column) )

# this one's by dictionary flags
#
        sql = "select count(*) from adit_item_tbl where tagcategory=? and %s='Y'"
        allflags = ("lclidflg", "lclsfidflg", "sfidflg")
        for table in tables :
            for column in allflags :
#                print (sql % (column,)), table,
                curs.execute( (sql % (column,)), (table,) )
                row = curs.fetchone()
#                print ":", row[0]
                if int( row[0] ) != 1 :
                    if column == "lclidflg" :
                        self._errors.append( "Table %s has %d %s tags but that's probably OK" % (table, int( row[0] ), column) )
                    else :
                        self._errors.append( "Table %s has %d %s tags" % (table, int( row[0] ), column) )
# metadata
#
        sql = "select tagcategory,count(distinct metadataflgs) from adit_item_tbl group by tagcategory"
        curs.execute( sql )
        while True :
            row = curs.fetchone()
#            if self.verbose : pprint.pprint( row )
            if row is None : break
            if row[1] != 1 :
                self._errors.append( "Table %s has invalid metadatalgs: %s values" % (row[0],row[1],) )

        curs.close()

# reserved words in tag and table names
# this is a list from some website or other of what various sql engines consider keywords
#
    def check_sql_keywords( self ) :
        if self.verbose : sys.stdout.write( self.__class__.__name__ + "._check_sql_keywords()\n" )
        RESERVED = ["ABS","ABSOLUTE","ACTION","ADMIN","AFTER","AGGREGATE","ALIAS","ALL","ALLOCATE",
"ALTER","ANALYSE","ANALYZE","AND","ANY","ARE","ARRAY","AS","ASC","ASENSITIVE","ASSERTION","ASYMMETRIC",
"AT","ATOMIC","AUTHORIZATION","AUTO_INCREMENT","AVG",
"BEFORE","BEGIN","BETWEEN","BIGINT","BINARY","BIT","BIT_LENGTH","BITVAR","BLOB","BOOLEAN","BOTH","BREADTH","BY",
"CALL","CALLED","CARDINALITY","CASCADE","CASE","CAST","CATALOG",
"CEIL","CEILING","CHAR","CHAR_LENGTH","CHARACTER","CHARACTER_LENGTH",
"CHECK","CLASS","CLOB","CLOSE","COALESCE","COLLATE","COLLATION","COLLECT","COLUMN",
"COMMIT","COMPLETION",
"CONDITION","CONNECT","CONNECTION","CONSTRAINT","CONSTRAINTS","CONSTRUCTOR","CONTINUE","CONVERT","CORR","CORRESPONDING",
"COUNT","COVAR_POP","COVAR_SAMP","CREATE","CROSS","CUBE","CUME_DIST","CURRENT","CURRENT_DATE",
"CURRENT_DEFAULT_TRANSFORM_GROUP","CURRENT_PATH","CURRENT_ROLE","CURRENT_TIME","CURRENT_TIMESTAMP","CURRENT_TRANSFORM_GROUP_FOR_TYPE",
"CURRENT_USER","CURSOR","CYCLE",
"DATA","DATE","DATETIME","DAY",
"DEALLOCATE","DEC","DECIMAL","DECLARE","DEFAULT","DEFERRABLE","DEFERRED",
"DELETE","DENSE_RANK","DEPTH","DEREF","DESC","DESCRIBE","DESCRIPTOR","DESTROY","DESTRUCTOR",
"DETERMINISTIC","DIAGNOSTICS","DICTIONARY","DISCONNECT","DISTINCT","DO","DOMAIN",
"DOUBLE","DROP","DYNAMIC","EACH","ELEMENT","ELSE",
"END","END-EXEC","EQUALS","ESCAPE","EVERY","EXCEPT","EXCEPTION",
"EXEC","EXECUTE","EXISTS","EXP","EXTERNAL","EXTRACT",
"FALSE","FETCH","FILTER",
"FIRST","FLOAT","FLOOR","FOR","FOREIGN","FOUND","FREE","FREEZE","FROM","FULL","FUNCTION","FUSION",
"GENERAL","GET","GLOBAL","GO","GOTO","GRANT","GREATEST",
"GROUP","GROUPING","HAVING","HOLD","HOST","HOUR",
"IDENTITY","IGNORE","ILIKE","IMMEDIATE",
"IN","INDICATOR","INITIALIZE","INITIALLY",
"INNER","INOUT","INPUT","INSENSITIVE","INSERT","INT","INTEGER",
"INTERSECT","INTERSECTION","INTERVAL","INTO","IS","ISNULL","ISOLATION","ITERATE",
"JOIN",
"LANGUAGE","LARGE","LAST","LATERAL","LEADING","LEFT","LESS","LEVEL","LIKE","LIMIT",
"LN","LOCAL","LOCALTIME","LOCALTIMESTAMP","LOCATOR","LOWER",
"MAP","MATCH","MAX","MEMBER","MERGE","METHOD","MIN","MINUTE","MOD","MODIFIES","MODIFY","MODULE","MULTISET",
"NAMES","NATIONAL","NATURAL","NCHAR","NCLOB","NEW","NEXT","NO","NONE","NORMALIZE","NOT","NOTNULL",
"NULL","NULLIF","NUMERIC",
"OBJECT","OCTET_LENGTH","OF","OFF","OFFSET","OLD","ON","ONLY","OPEN","OPERATION","OPTION",
"OR","ORDER","ORDINALITY","OUT","OUTER","OUTPUT","OVER","OVERLAPS","OVERLAY",
"PAD","PARAMETER","PARAMETER_SPECIFIC_SCHEMA","PARAMETERS","PARTIAL","PARTITION","PATH","PERCENT","PERCENT_RANK","PERCENTILE_CONT",
"PERCENTILE_DISC","PLACING","POSITION","POSTFIX","POWER","PRECISION","PREFIX","PREORDER","PREPARE","PRESERVE",
"PRIMARY","PRIOR","PRIVILEGES","PROCEDURE","PUBLIC",
"RANGE","RANK","READ","READS","REAL","RECURSIVE","REF","REFERENCES","REFERENCING","REGR_AVGX","REGR_AVGY",
"REGR_COUNT","REGR_INTERCEPT","REGR_R2","REGR_SLOPE","REGR_SXX","REGR_SXY","REGR_SYY","RELATIVE","RELEASE",
"RESTRICT","RESULT","RETURN",
"RETURNS","REVOKE","RIGHT","ROLE","ROLLBACK","ROUTINE",
"ROW","ROW_NUMBER","ROWID","ROWS",
"SAVEPOINT","SCHEMA","SCOPE","SCROLL","SEARCH","SECOND",
"SECTION","SELECT","SENSITIVE","SEQUENCE","SESSION","SESSION_USER",
"SET","SETOF","SETS","SIMILAR","SIZE","SMALLINT","SOME","SPACE",
"SPECIFIC","SPECIFICTYPE","SQL","SQLCODE","SQLERROR","SQLEXCEPTION",
"SQLSTATE","SQLWARNING","SQRT","START","STATE","STATEMENT","STATIC","STDDEV_POP","STDDEV_SAMP",
"STRUCTURE","SUBMULTISET","SUBSTRING",
"SUM","SYMMETRIC","SYSTEM","SYSTEM_USER",
"TABLE","TABLESAMPLE",
"TEMPORARY","TERMINATE","THAN","THEN","TIME","TIMESTAMP","TIMEZONE_HOUR","TIMEZONE_MINUTE",
"TO","TRAILING","TRANSACTION","TRANSLATE","TRANSLATION","TREAT","TRIGGER",
"TRIM","TRUE",
"UESCAPE","UNDER","UNION","UNIQUE",
"UNKNOWN","UNNEST","UPDATE","UPPER","USER","USING",
"VALUE","VALUES","VARCHAR","VARIABLE","VARYING","VAR_POP","VAR_SAMP",
"VERBOSE","VIEW",
"WHEN","WHENEVER","WHERE","WIDTH_BUCKET","WINDOW","WITH","WITHIN","WITHOUT","WORK","WRITE",
"YEAR","ZONE"]
        sql = "select distinct tagcategory,min(dictionaryseq) from adit_item_tbl " \
            + "group by tagcategory order by min(dictionaryseq)"
        curs = self._db.cursor()
        curs.execute( sql )
        while True :
            row = curs.fetchone()
            if row == None : break
            if str( row[0] ).strip().upper() in RESERVED :
                self._errors.append( "SQL reseved tag category: %s" % (row[0],) )

        sql = "select distinct tagfield,tagcategory,dictionaryseq from adit_item_tbl order by dictionaryseq"
        curs.execute( sql )
        while True :
            row = curs.fetchone()
            if row == None : break
            if str( row[0] ).strip().upper() in RESERVED :
                self._errors.append( "SQL reseved tag name: %s (_%s.%s)" % (row[0],row[1],row[0],) )

        curs.close()


####################################################################################################
#
if __name__ == "__main__" :

    props = ConfigParser.SafeConfigParser()
    props.read( sys.argv[1] )
    dbfile = props.get( "dictionary", "sqlite3.file" )
    if os.path.exists( dbfile ) : os.unlink( dbfile )
    db = DictDB.create_dictionary( props, verbose = False )

    if len( db._errors ) > 0 :
        for e in db._errors :
            sys.stderr.write( e + "\n" )
