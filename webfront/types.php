<?php

include_once $_SERVER["DOCUMENT_ROOT"] . "/php_includes/Globals.inc";
global $HTMLINCLUDES;
global $PDO_USER_PG;
global $PDO_PASSWD;
global $PDO_BMRBDSN_PG;

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

/* show list of ddl types */
    $sql = "select count(*) as cnt from dict.ddltypes";
    $query = $dbh->query( $sql, PDO::FETCH_ASSOC );
    $row = $query->fetch( PDO::FETCH_ASSOC );
    if( $row["cnt"] < 1 ) {
        echo "<h2>No supergroups found!</h2>";
    }
    else {
        echo "<h2>Data types</h2>\n";
        echo "<table border=\"0\" cellpadding=\"0\" cellspacing=\"0\" style=\"padding-left: 2em; padding-right: 2em;\">\n";
        echo "<tr style=\"background: #cbdbff;\">";
            echo "<th style=\"text-align: left; vertical-align: top; padding: 0.2em 1em 0.2em 1em;\">Data type</th>";
            echo "<th style=\"text-align: left; vertical-align: top; padding: 0.2em 1em 0.2em 1em;\">Regexp</th>";
            echo "<th style=\"text-align: left; vertical-align: top; padding: 0.2em 1em 0.2em 1em;\">Description</th>";
        echo "</tr>\n";
        $sql = "select ddltype,regexp,description from dict.ddltypes order by ddltype";
        $query = $dbh->query( $sql, PDO::FETCH_ASSOC );
        $even = TRUE;
        while( ($row = $query->fetch( PDO::FETCH_ASSOC )) ) {
            echo "<tr class=\"hiliteonhover\">\n";
            echo "<td style=\"text-align: left; vertical-align: top; padding: 0.5em;\">";
            echo "<a name=\"" . urlencode( $row["ddltype"] );
            echo "\">" . $row["ddltype"] . "</a></td>";
            echo "<td style=\"text-align: left; vertical-align: top; padding: 0.5em; white-space: nowrap;\">" . $row["regexp"] . "</td>";
            echo "<td style=\"text-align: left; vertical-align: top; padding: 0.5em;\">" . $row["description"] . "</td>";
            echo "</tr>\n";
        }
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