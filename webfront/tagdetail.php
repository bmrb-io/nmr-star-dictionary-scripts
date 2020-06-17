<?php

include_once $_SERVER["DOCUMENT_ROOT"] . "/php_includes/Globals.inc";
global $HTMLINCLUDES;
global $PDO_USER_PG;
global $PDO_PASSWD;
global $PDO_BMRBDSN_PG;

parse_str( $_SERVER['QUERY_STRING'], $params );

if( isset( $params["tag"] ) ) {
    $tag = trim( $params["tag"] );
    if( strlen( $tag ) < 1 ) 
        die( "Missing parameter" );
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

    $sql = "select originalcategory,tagcategory,tagfield,bmrbtype,description,"
         . "dbtype,dbnullable,primarykey,refkeygroup,reftable,refcolumn,"
         . "loopflag,rowindexflg,entryidflg,lclidflg,lclsfidflg,sfidflg,sfnameflg,sfcategoryflg,sfpointerflg,"
         . "adititemviewname,enumeratedflg,itemenumclosedflg,"
         . "defaultvalue,example,help,dictionaryseq from dict.val_item_tbl where originaltag=?";
    $query = $dbh->prepare( $sql );
    if( ! $query->execute( array( $tag ) ) )
        die( "Failed to run query.<br>Please report to webmaster@bmrb.wisc.edu" );

    if( ! ($row = $query->fetch( PDO::FETCH_ASSOC )) )
        echo "<h2>Tag " . $tag . " not found!</h2>";
    else {
        echo "<h2>" . $tag . "</h2>\n";
        echo "<table border=\"0\" cellpadding=\"0\" cellspacing=\"0\" style=\"padding-left: 2em; padding-right: 2em; width: 100%;\">\n";

        echo "<tr class=\"hiliteonhover\">\n";
        echo "<td style=\"text-align: left; vertical-align: top; padding: 0.2em 1em 0.2em 1em;\">Description</td>";
        echo "<td style=\"text-align: left; vertical-align: top; padding: 0.2em 1em 0.2em 1em;\">";
        echo $row["description"] . "</td>";
        echo "</tr>\n";

        echo "<tr>";
        echo "<td colspan=\"2\" style=\"text-align: left; vertical-align: top; padding: 0.2em 1em 0.2em 1em;\">Details:</td>";
        echo "</tr>\n";


        if( strtoupper( trim( $row["entryidflg"] ) ) == "Y" ) {
            echo "<tr class=\"hiliteonhover\">\n";
            echo "<td style=\"text-align: left; vertical-align: top; padding: 0.2em 1em 0.2em 1em;\">&nbsp;</td>";
            echo "<td style=\"text-align: left; vertical-align: top; padding: 0.2em 1em 0.2em 1em; font-weight: bold;\">entry ID</td>";
            echo "</tr>\n";
        }

        if( strtoupper( trim( $row["lclidflg"] ) ) == "Y" ) {
            echo "<tr class=\"hiliteonhover\">\n";
            echo "<td style=\"text-align: left; vertical-align: top; padding: 0.2em 1em 0.2em 1em;\">&nbsp;</td>";
            echo "<td style=\"text-align: left; vertical-align: top; padding: 0.2em 1em 0.2em 1em; font-weight: bold;\">";
            echo "\"local\" ID (unique within the entry)</td>";
            echo "</tr>\n";
        }

        if( strtoupper( trim( $row["lclsfidflg"] ) ) == "Y" ) {
            echo "<tr class=\"hiliteonhover\">\n";
            echo "<td style=\"text-align: left; vertical-align: top; padding: 0.2em 1em 0.2em 1em;\">&nbsp;</td>";
            echo "<td style=\"text-align: left; vertical-align: top; padding: 0.2em 1em 0.2em 1em; font-weight: bold;\">";
            echo "\"local\" saveframe ID (unique within the entry)</td>";
            echo "</tr>\n";
        }

        if( strtoupper( trim( $row["sfidflg"] ) ) == "Y" ) {
            echo "<tr class=\"hiliteonhover\">\n";
            echo "<td style=\"text-align: left; vertical-align: top; padding: 0.2em 1em 0.2em 1em;\">&nbsp;</td>";
            echo "<td style=\"text-align: left; vertical-align: top; padding: 0.2em 1em 0.2em 1em; font-weight: bold;\">";
            echo "\"global\" saveframe ID (unique within BMRB database)</td>";
            echo "</tr>\n";
        }

        if( strtoupper( trim( $row["sfnameflg"] ) ) == "Y" ) {
            echo "<tr class=\"hiliteonhover\">\n";
            echo "<td style=\"text-align: left; vertical-align: top; padding: 0.2em 1em 0.2em 1em;\">&nbsp;</td>";
            echo "<td style=\"text-align: left; vertical-align: top; padding: 0.2em 1em 0.2em 1em;\">";
            echo "<strong>name of the parent saveframe</strong> (necessary for NMR-STAR to relational database mapping)</td>";
            echo "</tr>\n";
        }

        if( strtoupper( trim( $row["sfcategoryflg"] ) ) == "Y" ) {
            echo "<tr class=\"hiliteonhover\">\n";
            echo "<td style=\"text-align: left; vertical-align: top; padding: 0.2em 1em 0.2em 1em;\">&nbsp;</td>";
            echo "<td style=\"text-align: left; vertical-align: top; padding: 0.2em 1em 0.2em 1em;\">";
            echo "<strong>category of the parent saveframe</strong> (necessary for NMR-STAR to relational database mapping)</td>";
            echo "</tr>\n";
        }

        if( strtoupper( trim( $row["sfpointerflg"] ) ) == "Y" ) {
            echo "<tr class=\"hiliteonhover\">\n";
            echo "<td style=\"text-align: left; vertical-align: top; padding: 0.2em 1em 0.2em 1em;\">&nbsp;</td>";
            echo "<td style=\"text-align: left; vertical-align: top; padding: 0.2em 1em 0.2em 1em; font-weight: bold;\">";
            echo "pointer to another saveframe in the entry</td>";
            echo "</tr>\n";
        }

        echo "<tr class=\"hiliteonhover\">\n";
        echo "<td style=\"text-align: left; vertical-align: top; padding: 0.2em 1em 0.2em 1em;\">Parent saveframe</td>";
        echo "<td style=\"text-align: left; vertical-align: top; padding: 0.2em 1em 0.2em 1em;\">";
        echo "<a href=\"tagcat.php?sfcat=" . urlencode( $row["originalcategory"] ) . "\">";
        echo $row["originalcategory"];
        echo "</a></td>";
        echo "</tr>\n";

        echo "<tr class=\"hiliteonhover\">\n";
        echo "<td style=\"text-align: left; vertical-align: top; padding: 0.2em 1em 0.2em 1em;\">Data type</td>";
        echo "<td style=\"text-align: left; vertical-align: top; padding: 0.2em 1em 0.2em 1em;\">";
        echo "<a href=\"types.php#" . urlencode( $row["bmrbtype"] ) . "\">";
        echo $row["bmrbtype"] . "</a></td>";
        echo "</tr>\n";

        if( strtoupper( trim( $row["itemenumclosedflg"] ) ) == "Y" ) {
            echo "<tr class=\"hiliteonhover\">\n";
            echo "<td class=\"expandingHeader NotSelected\" style=\"text-align: left; vertical-align: top; padding: 0.2em 1em 0.2em 1em;\">Allowed values</td>";
            echo "<td class=\"expandingBody\" style=\"text-align: left; vertical-align: top; padding: 0.2em 1em 0.2em 1em;\">";
            $qry2 = $dbh->prepare( "select val,seq from dict.enumerations where seq=? order by val" );
            if( ! ($qry2->execute( array( $row["dictionaryseq"] ) )) ) 
                echo "Enumeration not found";
            else {
                while( ($row2 = $qry2->fetch( PDO::FETCH_ASSOC )) )
                    echo $row2["val"] . "<br>";
            }
            echo "&nbsp;</td></tr>";
        }
        else if( strtoupper( trim( $row["enumeratedflg"] ) ) == "Y" ) {
            echo "<tr class=\"hiliteonhover\">\n";
            echo "<td class=\"expandingHeader NotSelected\" style=\"text-align: left; vertical-align: top; padding: 0.2em 1em 0.2em 1em;\">Common values</td>";
            echo "<td class=\"expandingBody\" style=\"text-align: left; vertical-align: top; padding: 0.2em 1em 0.2em 1em;\">";
            $qry2 = $dbh->prepare( "select val,seq from dict.enumerations where seq=? order by val" );
            if( ! ($qry2->execute( array( $row["dictionaryseq"] ) )) ) 
                echo "Enumeration not found";
            else {
                while( ($row2 = $qry2->fetch( PDO::FETCH_ASSOC )) )
                    echo $row2["val"] . "<br>";
            }
            echo "&nbsp;</td></tr>";
        }

        echo "<tr>";
        echo "<td colspan=\"2\" style=\"text-align: left; vertical-align: top; padding: 0.2em 1em 0.2em 1em;\">&nbsp;</td>";
        echo "</tr>\n";

        echo "<tr class=\"hiliteonhover\">\n";
        echo "<td style=\"text-align: left; vertical-align: top; padding: 0.2em 1em 0.2em 1em;\">DB table</td>";
        echo "<td style=\"text-align: left; vertical-align: top; padding: 0.2em 1em 0.2em 1em;\">";
        echo $row["tagcategory"] . "</td>";
        echo "</tr>\n";

        echo "<tr class=\"hiliteonhover\">\n";
        echo "<td style=\"text-align: left; vertical-align: top; padding: 0.2em 1em 0.2em 1em;\">DB column</td>";
        echo "<td style=\"text-align: left; vertical-align: top; padding: 0.2em 1em 0.2em 1em;\">";
        echo $row["tagfield"] . "</td>";
        echo "</tr>\n";

        echo "<tr class=\"hiliteonhover\">\n";
        echo "<td style=\"text-align: left; vertical-align: top; padding: 0.2em 1em 0.2em 1em;\">DB type</td>";
        echo "<td style=\"text-align: left; vertical-align: top; padding: 0.2em 1em 0.2em 1em;\">";
        echo $row["dbtype"] . "</td>";
        echo "</tr>\n";

        echo "<tr class=\"hiliteonhover\">\n";
        echo "<td style=\"text-align: left; vertical-align: top; padding: 0.2em 1em 0.2em 1em;\">NULL allowed</td>";
        echo "<td style=\"text-align: left; vertical-align: top; padding: 0.2em 1em 0.2em 1em;\">";
        if( strtoupper( trim( $row["dbnullable"] ) ) == "NOT NULL" ) 
            echo "<strong>no</strong> (mandatory)";
        else echo "yes";
        echo "</td>";
        echo "</tr>\n";

        if( strtoupper( trim( $row["primarykey"] ) ) == "Y" ) {
            echo "<tr class=\"hiliteonhover\">\n";
            echo "<td style=\"text-align: left; vertical-align: top; padding: 0.2em 1em 0.2em 1em;\">&nbsp;</td>";
            echo "<td style=\"text-align: left; vertical-align: top; padding: 0.2em 1em 0.2em 1em; font-weight: bold;\">part of primary key</td>";
            echo "</tr>\n";
        }

        if( strtoupper( trim( $row["rowindexflg"] ) ) == "Y" ) {
            echo "<tr class=\"hiliteonhover\">\n";
            echo "<td style=\"text-align: left; vertical-align: top; padding: 0.2em 1em 0.2em 1em;\">&nbsp;</td>";
            echo "<td style=\"text-align: left; vertical-align: top; padding: 0.2em 1em 0.2em 1em; font-weight: bold;\">row index for the table</td>";
            echo "</tr>\n";
        }
/*
        if( $row["refkeygroup"] != NULL ) {
//TODO: parse foreign key data
            echo "<tr class=\"hiliteonhover\">\n";
            echo "<td style=\"text-align: left; vertical-align: top; padding: 0.2em 1em 0.2em 1em;\">Parent tag(s)</td>";
            echo "<td style=\"text-align: left; vertical-align: top; padding: 0.2em 1em 0.2em 1em; font-weight: bold;\">";
            echo $row["reftable"];
            echo ".";
            echo $row["refcolumn"];
            echo "</td>";
            echo "</tr>\n";
        }
*/

        echo "<tr>";
        echo "<td colspan=\"2\" style=\"text-align: left; vertical-align: top; padding: 0.2em 1em 0.2em 1em;\">&nbsp;</td>";
        echo "</tr>\n";

        echo "<tr class=\"hiliteonhover\">\n";
        echo "<td style=\"text-align: left; vertical-align: top; padding: 0.2em 1em 0.2em 1em;\">Deposition system prompt</td>";
        echo "<td style=\"text-align: left; vertical-align: top; padding: 0.2em 1em 0.2em 1em;\">";
        echo $row["adititemviewname"] . "</td>";
        echo "</tr>\n";

        echo "<tr class=\"hiliteonhover\">\n";
        echo "<td style=\"text-align: left; vertical-align: top; padding: 0.2em 1em 0.2em 1em;\">Deposition system help</td>";
        echo "<td style=\"text-align: left; vertical-align: top; padding: 0.2em 1em 0.2em 1em;\">";
        echo $row["help"] . "</td>";
        echo "</tr>\n";

        echo "<tr class=\"hiliteonhover\">\n";
        echo "<td style=\"text-align: left; vertical-align: top; padding: 0.2em 1em 0.2em 1em;\">Example</td>";
        echo "<td style=\"text-align: left; vertical-align: top; padding: 0.2em 1em 0.2em 1em;\">";
        echo $row["example"] . "</td>";
        echo "</tr>\n";

        echo "<tr class=\"hiliteonhover\">\n";
        echo "<td style=\"text-align: left; vertical-align: top; padding: 0.2em 1em 0.2em 1em;\">Deposition system default</td>";
        echo "<td style=\"text-align: left; vertical-align: top; padding: 0.2em 1em 0.2em 1em;\">";
        echo $row["default"] . "</td>";
        echo "</tr>\n";

        echo "<tr>";
        echo "<td colspan=\"2\" style=\"text-align: left; vertical-align: top; padding: 0.2em 1em 0.2em 1em;\">&nbsp;</td>";
        echo "</tr>\n";

        echo "</table>\n";
//echo "<br><br>";
//        print_r( $row );
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
