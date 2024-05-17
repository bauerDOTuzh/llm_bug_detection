<?php
//set $per_page item as int number
    public function get_data($query = '')
    {
        $page_number = ($this->get_pagenum() - 1) * $this->limit;
        $orderby     = "ORDER BY {$this->tb_prefix}sms_subscribes.date DESC";
        $where       = "";

        if (isset($_REQUEST['orderby'])) {
            $orderby = "ORDER BY {$this->tb_prefix}sms_subscribes.{$_REQUEST['orderby']} {$_REQUEST['order']}";
        }

        if (!$query) {
            if (isset($_GET['group_id']) && $_GET['group_id']) {
                $group_id = sanitize_text_field($_GET['group_id']);
                $where    = "WHERE group_ID = {$group_id}";
            }

            if (isset($_GET['country_code']) && $_GET['country_code']) {
                $country_code = sanitize_text_field($_GET['country_code']);

                if ($where) {
                    $where .= " AND mobile LIKE '{$country_code}%'";
                } else {
                    $where = "WHERE mobile LIKE '{$country_code}%'";
                }
            }
            $query = $this->db->prepare("SELECT * FROM {$this->tb_prefix}sms_subscribes {$where} {$orderby} LIMIT %d OFFSET %d", $this->limit, $page_number);
        } else {
            $query .= $this->db->prepare(" LIMIT %d OFFSET %d", $this->limit, $page_number);
        }

        $result = $this->db->get_results($query, ARRAY_A);

        return $result;
    }
