<?php

include_once $_SERVER["DOCUMENT_ROOT"] . "/php_includes/Globals.inc";

global $HTMLINCLUDES;
global $PDO_USER_PG;
global $PDO_PASSWD;

global $PDO_BMRBDSN_PG; // = "pgsql:host=localhost;port=5432;dbname=bmrb";

parse_str( $_SERVER['QUERY_STRING'], $params );

if( isset( $params["tagcat"] ) ) {
    $tagcat = trim( $params["tagcat"] );
    if( strlen( $tagcat ) < 1 ) unset( $tagcat );
}

echo <<<EOT
<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN" "http://www.w3.org/TR/html4/loose.dtd">
<html lang="en_us">
<head>
    <meta http-equiv="content-type" content="text/html; charset=UTF-8">
    <meta http-equiv="refresh" content="84400">
    <title>NMR-STAR dictionary</title>
    <link rel="stylesheet" type="text/css" href="/stylesheets/newmain.css" title="stylesheet">
    <script type="text/javascript" src="/includes/jquery.js"></script>
    <script type="text/javascript" src="/includes/random_molecule.js"></script>
    <script type="text/javascript" src="/includes/expanding_menu.js"></script>
</head>
<body>
    <div id="wrapper">
EOT;

readfile( $HTMLINCLUDES . "/newheader.html" );

echo <<<EOT
    <table cellpadding="10px" cellspacing="0" class="content">
    <tr>
        <td id="leftcol" rowspan="2">
EOT;

readfile( $HTMLINCLUDES . "/newsidemenu.html" );

echo <<<EOT
        </td>
        <td id="maincol" style="text-align: center; width: 100%; height: 3em; padding-top: 1em;">
            <a href="supergrp.php">Supergroups</a> |
            <a href="sfcat.php">Saveframe categories</a> |
            <a href="tagcat.php">Tag categories</a> |
            <a href="tag.php">Tags</a> |
            <a href="types.php">Data types</a>

        </td>
     </tr>
    <tr>
        <td id="content" style="vertical-align: top; text-align: center;">
EOT;

try {
    $dbh = new PDO( $PDO_BMRBDSN_PG, $PDO_USER_PG, $PDO_PASSWD );
    $dbh->setAttribute( PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION );

    if( isset( $tagcat ) ) {
/* show tags in this category */
        $sql = "select count(*) as cnt from (select tagfield from dict.val_item_tbl"
             . " where tagcategory=?) as id";
        $query = $dbh->prepare( $sql );
        if( ! $query->execute( array( $tagcat ) ) )
            die( "Failed to run query.<br>Please report to webmaster@bmrb.wisc.edu" );
    }
    else {
/* show list of saveframe categories */
        $sql = "select count(*) as cnt from dict.val_item_tbl";
        if( ! ($query = $dbh->query( $sql, PDO::FETCH_ASSOC )) )
            die( "Failed to run query.<br>Please report to webmaster@bmrb.wisc.edu" );
    }

    $row = $query->fetch( PDO::FETCH_ASSOC );
    if( $row["cnt"] < 1 ) {
        echo "<h2>No tags";
        if( isset( $tagcat ) ) echo " in category " . $tagcat;
        echo " found!</h2>";
    }
    else {

        if( isset( $tagcat ) ) {

            echo "<h2>Tag category " . $tagcat . "</h2>\n";

            $sql = "select tagfield from dict.val_item_tbl where primarykey='Y' and tagcategory=?"
                 . " order by tagfield";
            $query = $dbh->prepare( $sql );
            if( ($query->execute( array( $tagcat ) )) ) {
                echo "<p style=\"text-align: left; padding-left: 2em; font-weight: bold;\">Key tags (columns):<ul style=\"text-align: left;\">";
                while( ($row = $query->fetch( PDO::FETCH_ASSOC )) ) {
                    echo "<li><a href=\"tagdetail.php?tag=_" . urlencode( $tagcat ) . "." . urlencode( $row["tagfield"] ) . "\">";
                    echo $row["tagfield"] . "</a></li>";
                }
                echo "</ul>\n";
            }
            $sql = "select tagfield,refkeygroup,reftable,refcolumn from dict.val_item_tbl where refkeygroup is not null and tagcategory=?"
                 . " order by tagfield";
            $query = $dbh->prepare( $sql );
            $fkeys = array();
            if( ($query->execute( array( $tagcat ) )) ) {
                while( ($row = $query->fetch( PDO::FETCH_ASSOC )) ) {
                    $fkeys[] = $row;
                }
            }
            if( sizeof( $fkeys ) > 0 ) {
/*
 * parse tuples like
 *  (1, table1, col1)
 *  (1;2, table1;table2, col2;col1)
 * into
 *  table1( col1, col2)
 *  table2( col1 )
 */
                $allgroups = array();
                $alltables = array();
                $allcols = array();
                $alltags = array();

                foreach( $fkeys as $row ) {
                    $grps = explode( ";", $row["refkeygroup"] );
                    for( $i = 0; $i < count( $grps ); $i++ ) {
                        if( ! in_array( $grps[$i], $allgroups ) )
                            $allgroups[] = $grps[$i];
                    }
                }
                foreach( $allgroups as $grp ) {
                    $alltags[$grp] = "";
                    $alltables[$grp] = "";
                    $allcols[$grp] = "";
                }

                foreach( $fkeys as $row ) {
// split on ';'
                    $grps = explode( ";", $row["refkeygroup"] );
                    $tbls = explode( ";", $row["reftable"] );
                    $cols = explode( ";", $row["refcolumn"] );

                    for( $i = 0; $i < count( $grps ); $i++ ) {
/*
echo "<br><em>checking group " . $i . " : " . $grps[$i] . "</em>";
echo "<br><em>tables " . $i . " : " . $tbls[$i] . "</em>";
echo "<br><em>columns " . $i . " : " . $cols[$i] . "</em>";
*/
                        $alltables[$grps[$i]] = $tbls[$i];
//echo "<br><em>alltables now</em>: ";
//print_r( $alltables );

                        $allcols[$grps[$i]] .= "<a href=\"tagdetail.php?tag=_";
                        $allcols[$grps[$i]] .= urlencode( $tbls[$i] ) . "." . urlencode( $cols[$i] );
                        $allcols[$grps[$i]] .= "\">" . $cols[$i] . "</a>, ";

//echo "<br><em>allcols now</em>: ";
//print_r( $allcols );

                        $alltags[$grps[$i]] .= "<a href=\"tagdetail.php?tag=_";
                        $alltags[$grps[$i]] .= urlencode( $tagcat ) . "." . urlencode( $row["tagfield"] );
                        $alltags[$grps[$i]] .= "\">" . $row["tagfield"] . "</a>, ";


//echo "<br><em>alltags now</em>: ";
//print_r( $alltags );
                    }
/*
echo "<br>";
print_r( $grps );
echo "<br>";
print_r( $tbls );
echo "<br>";
print_r( $cols );
echo "<br>";
print_r( $row );
echo "<br>";
*/
                }

                sort( $allgroups );

                echo "<p style=\"text-align: left; padding-left: 2em; font-weight: bold;\">Foreign key tags:";
                echo "<ul style=\"text-align: left;\">";

/*
print_r( $allgroups );
echo "<br>";
print_r( $alltags );
echo "<br>";
print_r( $alltables );
echo "<br>";
print_r( $allcols );
*/
                foreach( $allgroups as $grp ) {
                    echo "<li>";
                    echo "( " . rtrim( $alltags[$grp], ", " ) . " ) &rarr; ";
                    echo "<a href=\"tag.php?tagcat=" . urlencode( $alltables[$grp] ) . "\">";
                    echo $alltables[$grp] . "</a> ( ";
                    echo rtrim( $allcols[$grp], ", " ) . " )";
                    echo "</li>";
                }
                echo "</ul>";
            }
            echo "<p style=\"text-align: left; padding-left: 2em; font-weight: bold;\">Tags in table ";
            echo $tagcat . ":";
        }
        else 
            echo "<h2>All tags</h2>\n";

        echo "<table border=\"0\" cellpadding=\"0\" cellspacing=\"0\" style=\"padding-left: 2em; padding-right: 2em; width: 100%;\">\n";
        echo "<tr style=\"background: #cbdbff;\">";
        echo "<th style=\"text-align: left; vertical-align: top; padding: 0.2em 1em 0.2em 1em;\">Tag</th>";
        echo "<th style=\"text-align: left; vertical-align: top; padding: 0.2em 1em 0.2em 1em;\">Description</th>";
        echo "<th style=\"text-align: left; vertical-align: top; padding: 0.2em 1em 0.2em 1em;\">data type</th>";
        echo "<th style=\"text-align: left; vertical-align: top; padding: 0.2em 1em 0.2em 1em;\">Mandatory</th>";
        echo "</tr>";

        if( isset( $tagcat ) ) {
            $sql = "select tagcategory,tagfield,description,dbtype,bmrbtype,dbnullable"
                 . " from dict.val_item_tbl"
                 . " where tagcategory=?"
                 . " order by tagfield";
            $query = $dbh->prepare( $sql );
//echo $sql;
            if( ! $query->execute( array( $tagcat ) ) )
                die( "Failed to run query.<br>Please report to webmaster@bmrb.wisc.edu" );
        }
        else {
            $sql = "select tagcategory,tagfield,description,dbtype,bmrbtype,dbnullable"
                 . " from dict.val_item_tbl"
                 . " order by tagcategory,tagfield";

            if( ! ($query = $dbh->query( $sql, PDO::FETCH_ASSOC )) )
                die( "Failed to run query.<br>Please report to webmaster@bmrb.wisc.edu" );
        }
        while( ($row = $query->fetch( PDO::FETCH_ASSOC )) ) {

            echo "<tr class=\"hiliteonhover\">\n";

            echo "<td style=\"text-align: left; vertical-align: top; padding: 0.2em 1em 0.2em 1em;\">";
            echo "<a href=\"tagdetail.php?tag=";
            echo "_" . urlencode( $row["tagcategory"] ) . "." . urlencode( $row["tagfield"] );
            echo "\">";
            if( isset( $tagcat ) ) echo $row["tagfield"];
            else echo "_" . $row["tagcategory"] . "." . $row["tagfield"];
            echo "</a></td>";

            echo "<td style=\"text-align: left; vertical-align: top; padding: 0.2em 1em 0.2em 1em;\">";
            echo $row["description"] . "</td>";

            echo "<td style=\"text-align: left; vertical-align: top; padding: 0.2em 1em 0.2em 1em;\">";
            echo "<a href=\"types.php#" . urlencode( $row["bmrbtype"] );
            echo "\">" . $row["bmrbtype"] . "</a></td>";

            if( strtoupper( trim( $row["dbnullable"] ) ) == "NOT NULL" )
                echo "<td style=\"text-align: left; vertical-align: top; padding: 0.2em 1em 0.2em 1em; font-weight: bold;\">yes</td>";
            else
                echo "<td style=\"text-align: left; vertical-align: top; padding: 0.2em 1em 0.2em 1em;\">&nbsp;</td>";

            echo "</tr>\n";
        } // endwhile

            echo "<tr>\n";
            echo "<td colspan=\"4\">&nbsp;</td>";
            echo "</tr>\n";
        echo "</table>\n";
    }
    $query = NULL;
    $dbh = NULL;

    echo "</td>\n</tr>\n</table>\n";
    readfile( $HTMLINCLUDES . "/newfooter.html" );
    echo "</div>\n</body>\n</html>\n";

}
catch( PDOException $e ) {
    echo( "PDO exception " . $e->getMessage() . "<br>\n" );
    echo $dbh->errorCode() . "<br>\n";
    echo $e->getTraceAsString() . "<br>\n";
    die( "Please report to webmaster@bmrb.wisc.edu" );
}
?>
