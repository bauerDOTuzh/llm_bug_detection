<?php
function sanitize($data) {
    global $fmdb;
    
    if (is_string($data)) {
        if ($fmdb->use_mysqli) {
            return @mysqli_real_escape_string($fmdb->dbh, $data);
        } else {
            return @mysql_real_escape_string($data);
        }
    }
    return $data;
}
