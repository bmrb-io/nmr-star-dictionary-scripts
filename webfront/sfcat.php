<?php

include_once $_SERVER["DOCUMENT_ROOT"] . "/php_includes/Globals.inc";
global $HTMLINCLUDES;
global $PDO_USER_PG;
global $PDO_PASSWD;
global $PDO_BMRBDSN_PG;

parse_str( $_SERVER['QUERY_STRING'], $params );

if( isset( $params["supergroup"] ) ) {
    $supergroup = trim( $params["supergroup"] );
    if( strlen( $supergroup ) < 1 ) unset( $supergroup );
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

    if( isset( $supergroup ) ) {
/* show saveframe categories in this supergroup */
        $sql = "select count(*) as cnt from (select c.groupid from dict.aditcatgrp c"
             . " join dict.aditsupergrp s on c.supergrpid=s.supergrpid"
             . " where s.supergrpname=?) as id";
        $query = $dbh->prepare( $sql );
//print $sql;
        if( ! $query->execute( array( $supergroup ) ) )
            die( "Failed to run query.<br>Please report to webmaster@bmrb.wisc.edu" );
    }
    else {
/* show list of saveframe categories */
        $sql = "select count(*) as cnt from dict.aditcatgrp";
        $query = $dbh->query( $sql, PDO::FETCH_ASSOC );
    }

    $row = $query->fetch( PDO::FETCH_ASSOC );
    if( $row["cnt"] < 1 ) {
        echo "<h2>No saveframes";
        if( isset( $supergroup ) ) echo " in supergroup " . $supergroup;
        echo " found!</h2>";
    }
    else {
        echo "<h2>Saveframe categories";
        if( isset( $supergroup ) ) echo " in group " . $supergroup;
        echo "</h2>\n";

        echo "<table border=\"0\" cellpadding=\"0\" cellspacing=\"0\" style=\"padding-left: 2em; padding-right: 2em; width: 100%;\">\n";
        echo "<tr style=\"background: #cbdbff;\">";
        echo "<th style=\"text-align: left; vertical-align: top; padding: 0.2em 1em 0.2em 1em;\">Category</th>";
        echo "<th style=\"text-align: left; vertical-align: top; padding: 0.2em 1em 0.2em 1em;\">Description</th>";
        echo "</tr>";

/*
 * TODO: add saveframe category description (not c.catgrpviewhelp) to the dictionary
 * (also in the full list below)
 */

        if( isset( $supergroup ) ) {
            $sql = "select c.sfcategory,c.catgrpviewname,c.mandatorynumber,c.aditreplicable,c.groupid"
                 . " from dict.aditcatgrp c join dict.aditsupergrp s on c.supergrpid=s.supergrpid"
                 . " where s.supergrpname=? order by c.sfcategory"; //c.groupid";
            $query = $dbh->prepare( $sql );
//echo $sql;
            if( ! $query->execute( array( $supergroup ) ) )
                die( "Failed to run query.<br>Please report to webmaster@bmrb.wisc.edu" );
        }
        else {
            $sql = "select sfcategory,catgrpviewname,mandatorynumber,aditreplicable,supergrpid,groupid"
                 . " from dict.aditcatgrp order by sfcategory"; // supergrpid,groupid";
            if( ! ($query = $dbh->query( $sql, PDO::FETCH_ASSOC )) )
                die( "Failed to run query.<br>Please report to webmaster@bmrb.wisc.edu" );
        }

        while( ($row = $query->fetch( PDO::FETCH_ASSOC )) ) {
            echo "<tr class=\"hiliteonhover\">\n";
            echo "<td style=\"text-align: left; vertical-align: top; padding: 0.2em 1em 0.2em 1em;\">";
            echo "<a href=\"tagcat.php?sfcat=" . urlencode( $row["sfcategory"] );
            echo "\">" . $row["sfcategory"] . "</a></td>";

            echo "<td style=\"text-align: left; vertical-align: top; padding: 0.2em 1em 0.2em 1em;\">";
            echo $row["catgrpviewname"] . "</td>";
/*
 * TODO: query the validation table and add "conditional"
 * "<td style=\"text-align: left; vertical-align: top; padding: 0.2em 1em 0.2em 1em; font-style: italic;\">conditional</td>";
 * (also in the full list below)
 */
/* TODO: figure out how to display adit-mandatory vs released-mandatory
                if( ($row["mandatorynumber"] != NULL) && ($row["mandatorynumber"] > 0) )
                    echo "<td style=\"text-align: left; vertical-align: top; padding: 0.2em 1em 0.2em 1em; font-weight: bold;\">required</td>";
                else 
                    echo "<td style=\"text-align: left; vertical-align: top; padding: 0.2em 1em 0.2em 1em;\">optional</td>";

                if( strtoupper( trim( $row["aditreplicable"] ) ) == 'N' )
                    echo "<td style=\"text-align: left; vertical-align: top; padding: 0.2em 1em 0.2em 1em;\">only one saveframe allowed in an entry</td>";
                else
                    echo "<td style=\"text-align: left; vertical-align: top; padding: 0.2em 1em 0.2em 1em;\">&nbsp;</td>";
*/
            echo "</tr>\n";
        } //endwhile resultset
        echo "</table>\n";

    } // endif $supergroup

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