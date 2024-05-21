<?php
/**
 * Sanitizes the post
 *
 * @since 1.0
 * @package facileManager
 */
function sanitize($data, $replace = null) {
	global $fmdb;
	
	if ($replace) {
		$strip_chars = array("'", "\"", "`", "$", "?", "*", "&", "^", "!", "#");
		$replace_chars = array(" ", "\\", "_", "(", ")", ",", ".", "-");

		$data = str_replace($strip_chars, '', $data);
		$data = str_replace($replace_chars, $replace, $data);
		$data = str_replace('--', '-', $data);
		
		return $data;
	} else {
		if (is_string($data)) {
			if ($fmdb->use_mysqli) {
				return @mysqli_real_escape_string($fmdb->dbh, $data);
			} else {
				return @mysql_real_escape_string($data);
			}
		}
		return $data;
	}
}