<?php
{prepend_content}
protected function get_response_file_data(&$model, &$response) {

    $response['data']['path'] = $model->path;
    $response['data']['size'] = $model->fsFile->size();
    $response['data']['extension'] = strtolower($model->fsFile->extension());
    $response['data']['handler']='startjs:function(){'.$model->getDefaultHandler()->getHandler($model).'}:endjs';

}
{append_content}