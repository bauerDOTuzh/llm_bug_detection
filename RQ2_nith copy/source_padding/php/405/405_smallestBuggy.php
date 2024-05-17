<?php
{prepend_content}
public function get_data($query)
{
    $where = "";

    if (isset($_GET['group_id']) && $_GET['group_id']) {
        $group_id = sanitize_text_field($_GET['group_id']);
        $where = "WHERE group_ID = {$group_id}";
    }

    if (isset($_GET['country_code']) && $_GET['country_code']) {
        $country_code = sanitize_text_field($_GET['country_code']);
        $where .= " AND mobile LIKE '{$country_code}%'";
    }
    $query = $this->db->prepare("SELECT * FROM {$this->tb_prefix}sms_subscribes {$where}");

    return $this->db->get_results($query);
}
{append_content}