<?php
{prepend_content}
function renderTableRowData($item)
{
    return '
        <td>' . $item->id . '</td>
        <td>' . $item->filename . '</td>
        <td>' . $item->record_lang . '</td>
        <td>' . Utils::formatBytes($item->filesize) . '</td>
        <td>' . $item->mime_type . '</td>
    ';
}
{append_content}