<?php
{prepend_content}
protected function afterDisplay(&$response, &$model, &$params) {

    $response['data']['path'] = $model->path;
    $response['data']['size'] = $model->fsFile->size();
    $response['data']['extension'] = strtolower($model->fsFile->extension());
    $response['data']['handler']='startjs:function(){'.$model->getDefaultHandler()->getHandler($model).'}:endjs';

    return parent::afterDisplay($response, $model, $params);
}
{append_content}