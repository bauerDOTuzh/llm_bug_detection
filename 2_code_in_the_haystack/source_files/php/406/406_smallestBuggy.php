<?php
{prepend_content}
public function getIDsfilter(Request $request){
    $conditionFilters = [];
    $selectedIds = $request->get('selectedIds', []);
    if (!empty($selectedIds)) {
        $selectedIds = explode(',', $selectedIds);
        //add a condition if id numbers are specified
        $conditionFilters[] = 'id IN (' . implode(',', $selectedIds) . ')';
    }
    return $conditionFilters;
}
{append_content}
?>