<?php
protected function afterDisplay(&$response, &$model, &$params) {

    $response['data']['path'] = $model->path;
    $response['data']['size'] = $model->fsFile->size();
    $response['data']['extension'] = strtolower($model->fsFile->extension());
    $response['data']['type'] = \GO::t($response['data']['extension'], 'base', 'filetypes');

    $response['data']['locked_user_name']=$model->lockedByUser ? $model->lockedByUser->name : '';
    $response['data']['locked']=$model->isLocked();
    $response['data']['unlock_allowed']=$model->unlockAllowed();


    if (!empty($model->random_code) && time() < $model->expire_time) {
        $response['data']['expire_time'] = \GO\Base\Util\Date::get_timestamp(\GO\Base\Util\Date::date_add($model->expire_time, -1),false);
        $response['data']['download_link'] = $model->emailDownloadURL;
    } else {
        $response['data']['expire_time'] = "";
        $response['data']['download_link'] = "";
    }

    $response['data']['url']=\GO::url('files/file/download',array('id'=>$model->id), false, true);

    if ($model->fsFile->isImage()) {
        if($response['data']['extension'] == 'gif' && $this->isAnimatedGif(\GO::config()->file_storage_path . $model->path)) {
            $response['data']['thumbnail_url'] = $model->getDownloadURL(false);
        } else {
            $response['data']['thumbnail_url'] = $model->thumbURL;
        }
    }else
        $response['data']['thumbnail_url'] = "";

    $response['data']['handler']='startjs:function(){'.$model->getDefaultHandler()->getHandler($model).'}:endjs';

    try{
        if(\GO::modules()->filesearch){
            $filesearch = \GO\Filesearch\Model\Filesearch::model()->findByPk($model->id);
    //				if(!$filesearch){
    //					$filesearch = \GO\Filesearch\Model\Filesearch::model()->createFromFile($model);
    //				}
            if($filesearch){
                $response['data']=array_merge($filesearch->getAttributes('formatted'), $response['data']);
            

                if (!empty($params['query_params'])) {
                    $qp = json_decode($params['query_params'], true);
                    if (isset($qp['content_all'])){

                        $c = new \GO\Filesearch\Controller\FilesearchController();

                        $response['data']['text'] = $c->highlightSearchParams($qp, $response['data']['text']);
                    }
                }
            }else
            {
                $response['data']['text'] = \GO::t("This file has not been indexed yet", "filesearch");
            }
        }
    }
    catch(\Exception $e){
        \GO::debug((string) $e);
        
        $response['data']['text'] = "Index out of date. Please rebuild it using the admin tools.";
    }

    return parent::afterDisplay($response, $model, $params);
}