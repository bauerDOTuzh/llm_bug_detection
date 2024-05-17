<?php
{prepend_content}
public function downloadAsZipAddFilesAction($request){
    $conditionFilters = [];
    $selectedIds = $request->get('selectedIds', []);
    if (!empty($selectedIds)) {
        $selectedIds = explode(',', $selectedIds);
        //add a condition if id numbers are specified
        $conditionFilters[] = 'id IN (' . implode(',', $selectedIds) . ')';
    }
    $condition = implode(' AND ', $conditionFilters);
    $assetList = new Asset\Listing();
    $assetList->setCondition($condition);
}
{append_content}
?>