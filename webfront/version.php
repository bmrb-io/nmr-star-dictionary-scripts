<?php

include_once $_SERVER["DOCUMENT_ROOT"] . "/php_includes/Globals.inc";

global $PDO_USER_PG;
global $PDO_PASSWD;
global $PDO_BMRBDSN_PG;

try {
    $dbh = new PDO( $PDO_BMRBDSN_PG, $PDO_USER_PG, $PDO_PASSWD );
    $dbh->setAttribute( PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION );

    $sql = "select defaultvalue from dict.val_item_tbl ";
    $sql .= "where originaltag='_Entry.NMR_STAR_version'";

    $query = $dbh->query( $sql, PDO::FETCH_ASSOC );
    if( ($row = $query->fetch( PDO::FETCH_ASSOC )) )
	echo $row["defaultvalue"];
    else echo "3.1";
    $query = NULL;
    $dbh = NULL;
}
catch( PDOException $e ) {
    echo( "PDO exception " . $e->getMessage() . "<br>\n" );
    echo $dbh->errorCode() . "<br>\n";
    echo $e->getTraceAsString() . "<br>\n";
    die( "Please report to webmaster@bmrb.wisc.edu" );
}
?>