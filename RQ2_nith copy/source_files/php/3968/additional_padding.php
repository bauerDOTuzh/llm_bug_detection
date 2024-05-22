<?php

// -x-
protected $model = 'GO\Files\Model\Bookmark';
// -x-
protected function beforeSubmit(&$response, &$model, &$params) {
    // See if folder with this ID can be accessed.
    $folderModel = \GO\Files\Model\Folder::model()->findByPk($params['folder_id']);
    
    if (empty($folderModel))
        return false;		
    
    $params['user_id'] = $model->user_id = \GO::user()->id;
    
    $response['user_id'] = \GO::user()->id;
    $response['folder_id'] = $folderModel->id;
    
    return parent::beforeSubmit($params, $folderModel, $params);
}
// -x-
public function formatStoreRecord($record, $model, $store) {
    $record['folder_id'] = $model->folder_id;
    $record['name'] = $model->folder->name;
    return parent::formatStoreRecord($record, $model, $store);
}
// -x-
protected function actionDelete($params) {
    
    $pk = array('user_id' => \GO::user()->id, 'folder_id' => $params['folder_id']);
    
    
    $model = \GO\Files\Model\Bookmark::model()->findByPk($pk);
    
//		$response = array();
//		$response = $this->beforeDelete($response, $model, $params);
    $response['success'] = $model->delete();
//		$response = $this->afterDelete($response, $model, $params);

    return $response;
}
// -x-
protected function beforeStoreStatement(array &$response, array &$params, \GO\Base\Data\AbstractStore &$store, \GO\Base\Db\FindParams $storeParams) {
    $storeParams
        ->select('`t`.`folder_id`,`t`.`user_id`,`f`.`name`')
        ->joinModel(array(
            'model'=>'GO\Files\Model\Folder',
            'localTableAlias'=>'t',
            'localField'=>'folder_id',
            'foreignField'=>'id',
            'tableAlias'=>'f'
        ))
        ->getCriteria()->addCondition('user_id',\GO::user()->id);
    return parent::beforeStoreStatement($response, $params, $store, $storeParams);
}
// -x-
protected $model = 'GO\Files\Model\Template';
// -x-
protected function beforeSubmit(&$response, &$model, &$params) {

    if (isset($_FILES['attachments']['tmp_name'][0]) && is_uploaded_file($_FILES['attachments']['tmp_name'][0])) {
        $file = new \GO\Base\Fs\File($_FILES['attachments']['tmp_name'][0]);
        $fileWithName = new \GO\Base\Fs\File($_FILES['attachments']['name'][0]);
        $model->content = $file->contents();
        $model->extension = $fileWithName->extension();
    } else {
        $response['validationErrors'] = array('attachments'=> \GO::t("files", "uploadFailed"));
        $response['success'] = false;
        $response['feedback'] = \GO::t("The upload failed! Ask the server manager for what wrong", "files");
        return false;
    }
    

    return parent::beforeSubmit($response, $model, $params);
}
// -x-
protected function formatColumns(\GO\Base\Data\ColumnModel $columnModel) {
    
    $columnModel->formatColumn('type', 'GO\Base\Fs\File::getFileTypeDescription($model->extension)');
    
    return parent::formatColumns($columnModel);
}
// -x-
protected function getStoreExcludeColumns() {
    return array('content');
}
// -x-
protected function afterLoad(&$response, &$model, &$params) {
    
    unset($response['data']['content']);
    
    return parent::afterLoad($response, $model, $params);
}
// -x-
protected function beforeStore(&$response, &$params, &$store) {
    $store->setDefaultSortOrder('name','ASC');
    return parent::beforeStore($response, $params, $store);
}
// -x-
protected function actionDownload($params){
    $template = \GO\Files\Model\Template::model()->findByPk($params['id']);
    
    \GO\Base\Util\Http::outputDownloadHeaders(new \GO\Base\Fs\File($template->name.'.'.$template->extension));
    
    echo $template->content;
}
// -x-
protected function actionCreateFile($params){
    
    $filename = \GO\Base\Fs\File::stripInvalidChars($params['filename']);
    if(empty($filename))
        throw new \Exception("Filename can not be empty");
    
    $template = \GO\Files\Model\Template::model()->findByPk($params['template_id']);
    
    $folder = \GO\Files\Model\Folder::model()->findByPk($params['folder_id']);
    
    $path = \GO::config()->file_storage_path.$folder->path.'/'.$filename;
    if(!empty($template->extension))
        $path .= '.'.$template->extension;
    
    $fsFile = new \GO\Base\Fs\File($path);
    $fsFile->putContents($template->content);
    
    $fileModel = \GO\Files\Model\File::importFromFilesystem($fsFile);
    if(!$fileModel)
    {
        throw new Exception("Could not create file");
    }
    return array('id'=>$fileModel->id, 'success'=>true);
}
// -x-
protected $model = 'GO\Files\Model\Version';
// -x-
protected function actionDownload($params){
    $version = \GO\Files\Model\Version::model()->findByPk($params['id']);
    $file = $version->getFilesystemFile();
    \GO\Base\Util\Http::outputDownloadHeaders($file);
    $file->output();
}
// -x-
/**
 * Will find all versioning files and put the filesize in the database
 */
protected function actionRecalculate() {
    $fp = FindParams::newInstance()->ignoreAcl();
    $stmt = Version::model()->find($fp);
    
    $success = 0; $failed = 0;
    while($version = $stmt->fetch()) {
        $path = \GO::config()->file_storage_path.$version->path;
        if(file_exists($path)) {
            $pdo_statement = \GO::getDbConnection()->query('UPDATE '.Version::model()->tableName(). ' SET `size_bytes` = '.filesize($path).';');
            if($pdo_statement->execute()) {
                $success++;
            } else
                $failed++;
        }
    }
    echo $success.' Done<br> '.$failed. ' Failed';
}
// -x-
protected function getStoreParams($params) {		
    $findParams = \GO\Base\Db\FindParams::newInstance()->ignoreAcl();
    $findParams->getCriteria()->addCondition('file_id', $params['file_id']);		
    
    return $findParams;
}
// -x-
protected function formatColumns(\GO\Base\Data\ColumnModel $columnModel) {
    
    $columnModel->formatColumn('user_name', '$model->user->name');
    
    return parent::formatColumns($columnModel);
}
// -x-
public function enableUserAndGroupSupport() {
    return false;
}

public function getLabel() {
    return "Set the correct quota user to each folder";
}

public function getDescription() {
    return "This have to save every folder once. and could take some time";
}

/**
 * The code that needs to be called when the cron is running
 * 
 * If $this->enableUserAndGroupSupport() returns TRUE then the run function 
 * will be called for each $user. (The $user parameter will be given)
 * 
 * If $this->enableUserAndGroupSupport() returns FALSE then the 
 * $user parameter is null and the run function will be called only once.
 * 
 * @param \GO\Base\Cron\CronJob $cronJob
 */
public function run(\GO\Base\Cron\CronJob $cronJob) {
    $controller = new \GO\Files\Controller\FileController();
    $controller->run('CorrectQuotaUser');
}
// -x-
/**
 * Return true or false to enable the selection for users and groups for
 * this cronjob.
 *
 * @return bool
 */
public function enableUserAndGroupSupport()
{
    return false;
}

/**
 * Get the unique name of the Cronjob
 *
 * @return StringHelper
 */
public function getLabel()
{
    return GO::t("Delete expired download link files", "files");
}

/**
 * Get the unique name of the Cronjob
 *
 * @return StringHelper
 */
public function getDescription()
{
    return GO::t("Delete download link files that are no longer valid", "files");
}

/**
 * The code that needs to be called when the cron is running
 *
 * @param GO\Base\Cron\CronJob $cronJob
 */
public function run(GO\Base\Cron\CronJob $cronJob)
{
        
        $filesStmt = File::model()->find(
            FindParams::newInstance()
                ->ignoreAcl()
                ->criteria(FindCriteria::newInstance()
                    ->addCondition('expire_time',time(),'<')
                    ->addCondition('expire_time','0','>')
                    ->addCondition('random_code','','!=')
                    ->addCondition('delete_when_expired','1')
                )
        );
        
        foreach ($filesStmt as $fileModel)
            $fileModel->delete();
        
}
// -x-
