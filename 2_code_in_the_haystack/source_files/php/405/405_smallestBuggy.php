<?php
{prepend_content}
public function mobile_or_country_query($where)
{
    if (isset($_GET['group_id']) && $_GET['group_id']) {
        $group_id = sanitize_text_field($_GET['group_id']);
        $where = "WHERE group_ID = {$group_id}";
    }

    if (isset($_GET['country_code']) && $_GET['country_code']) {
        $country_code = sanitize_text_field($_GET['country_code']);
        if ($where) {
            $where .= " AND mobile LIKE '{$country_code}%'";
        } else {
            $where = "WHERE mobile LIKE '{$country_code}%'";
        }
    }
    return $where;
}
{append_content}