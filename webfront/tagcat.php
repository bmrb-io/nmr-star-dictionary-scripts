<?php

include_once $_SERVER["DOCUMENT_ROOT"] . "/php_includes/Globals.inc";
global $HTMLINCLUDES;
global $PDO_USER_PG;
global $PDO_PASSWD;
global $PDO_BMRBDSN_PG;

parse_str( $_SERVER['QUERY_STRING'], $params );

if( isset( $params["sfcat"] ) ) {
    $sfcat = trim( $params["sfcat"] );
    if( strlen( $sfcat ) < 1 ) unset( $sfcat );
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

    if( isset( $sfcat ) ) {
/* show tag categories in this saveframe category */
        $sql = "select count(*) as cnt from (select distinct tagcategory from dict.val_item_tbl"
             . " where originalcategory=?) as id";
        $query = $dbh->prepare( $sql );
        if( ! $query->execute( array( $sfcat ) ) )
            die( "Failed to run query.<br>Please report to webmaster@bmrb.wisc.edu" );
    }
    else {
/* show list of tag categories */
        $sql = "select count(*) as cnt from dict.val_item_tbl";
        if( ! ($query = $dbh->query( $sql, PDO::FETCH_ASSOC )) )
            die( "Failed to run query.<br>Please report to webmaster@bmrb.wisc.edu" );
    }
    $row = $query->fetch( PDO::FETCH_ASSOC );
    if( $row["cnt"] < 1 ) {
        echo "<h2>No tag categories";
        if( isset( $sfcat ) ) echo " in saveframe " . $sfcat;
        echo " found!</h2>";
    }
    else {
        echo "<h2>Tag categories (tables)";
        if( isset( $sfcat ) ) echo " in saveframe " . $sfcat;
        echo "</h2>\n";

        echo "<table border=\"0\" cellpadding=\"0\" cellspacing=\"0\" style=\"padding-left: 2em; padding-right: 2em; width: 100%;\">\n";
        echo "<tr style=\"background: #cbdbff;\">";
        echo "<th style=\"text-align: left; vertical-align: top; padding: 0.2em 1em 0.2em 1em;\">Tag category</th>";
        echo "<th style=\"text-align: left; vertical-align: top; padding: 0.2em 1em 0.2em 1em;\">Parent category</th>";
        echo "<th style=\"text-align: left; vertical-align: top; padding: 0.2em 1em 0.2em 1em;\">Description</th>";
        echo "<th style=\"text-align: left; vertical-align: top; padding: 0.2em 1em 0.2em 1em;\">Loop table</th>";
        echo "</tr>\n";

/*
 * TODO: add saveframe category description (not adit view text) to the dictionary?
 * (also in the full list below)
 */
        if( isset( $sfcat ) ) {
/*
            $sql = "select tagcategory,aditcatviewname,min(dictionaryseq)"
                 . " from dict.val_item_tbl"
                 . " where originalcategory=?" 
                 . " group by tagcategory,aditcatviewname"
                 . " order by min(dictionaryseq)";
*/
            $sql = "select distinct tagcategory,aditcatviewname,loopflag,originalcategory"
                 . " from dict.val_item_tbl"
                 . " where originalcategory=?"
                 . " order by tagcategory";
            $query = $dbh->prepare( $sql );
            if( ! $query->execute( array( $sfcat ) ) )
                die( "Failed to run query.<br>Please report to webmaster@bmrb.wisc.edu" );
        }
        else {
/*
            $sql = "select tagcategory,aditcatviewname,min(dictionaryseq)"
                 . " from dict.val_item_tbl"
                 . " group by tagcategory,aditcatviewname"
                 . " order by min(dictionaryseq)";
*/
            $sql = "select distinct tagcategory,aditcatviewname,loopflag,originalcategory"
                 . " from dict.val_item_tbl"
                 . " order by tagcategory";
            if( ! ($query = $dbh->query( $sql, PDO::FETCH_ASSOC )) )
                die( "Failed to run query.<br>Please report to webmaster@bmrb.wisc.edu" );
        }
        $even = TRUE;
        while( ($row = $query->fetch( PDO::FETCH_ASSOC )) ) {
            echo "<tr class=\"hiliteonhover\">\n";
            echo "<td style=\"text-align: left; vertical-align: top; padding: 0.2em 1em 0.2em 1em;\">";
            echo "<a href=\"tag.php?tagcat=" . urlencode( $row["tagcategory"] );
            echo "\">" . $row["tagcategory"] . "</a></td>";

            echo "<td style=\"text-align: left; vertical-align: top; padding: 0.2em 1em 0.2em 1em;\">";
//            echo "<a href=\"sfcat.php?sfcat=" . urlencode( $row["originalcategory"] );
//            echo "\">" . 
            echo $row["originalcategory"];
//            echo "</a>";
            echo "</td>";


            echo "<td style=\"text-align: left; vertical-align: top; padding: 0.2em 1em 0.2em 1em;\">";
            echo $row["aditcatviewname"] . "</td>";

            if( strtoupper( trim( $row["loopflag"] ) ) == "N" )
                echo "<td style=\"text-align: left; vertical-align: top; padding: 0.2em 1em 0.2em 1em;\">no</td>";
            else
                echo "<td style=\"text-align: left; vertical-align: top; padding: 0.2em 1em 0.2em 1em;\">&nbsp;</td>";


/*
TODO: get mandatory number from validation table
                if( $row["mandatorynumber"] != NULL )
                    echo "<td style=\"text-align: left; vertical-align: top; padding: 0.2em 1em 0.2em 1em; font-style: italic;\">required</td>";
                else 
                    echo "<td style=\"text-align: left; vertical-align: top; padding: 0.2em 1em 0.2em 1em;\">optional</td>";
*/
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