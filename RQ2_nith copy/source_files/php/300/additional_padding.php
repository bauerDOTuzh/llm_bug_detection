<?php

/**
 * Private phpMyFAQ Admin API: handles an attachment with the given id.
 *
 * This Source Code Form is subject to the terms of the Mozilla Public License,
 * v. 2.0. If a copy of the MPL was not distributed with this file, You can
 * obtain one at https://mozilla.org/MPL/2.0/.
 *
 * @package   phpMyFAQ
 * @author    Anatoliy Belsky <anatoliy.belsky@mayflower.de>
 * @copyright 2010-2023 phpMyFAQ Team
 * @license   https://www.mozilla.org/MPL/2.0/ Mozilla Public License Version 2.0
 * @link      https://www.phpmyfaq.de
 * @since     2010-12-20
 */

use phpMyFAQ\Attachment\AttachmentException;
use phpMyFAQ\Attachment\AttachmentFactory;
use phpMyFAQ\Filter;
use phpMyFAQ\Session\Token;
use phpMyFAQ\Translation;
use Symfony\Component\HttpFoundation\JsonResponse;
use Symfony\Component\HttpFoundation\Request;
use Symfony\Component\HttpFoundation\Response;

if (!defined('IS_VALID_PHPMYFAQ')) {
    http_response_code(400);
    exit();
}

//
// Create Request & Response
//
$response = new JsonResponse();
$request = Request::createFromGlobals();

$ajaxAction = Filter::filterVar($request->query->get('ajaxaction'), FILTER_SANITIZE_SPECIAL_CHARS);
$attId = Filter::filterVar($request->query->get('attId'), FILTER_VALIDATE_INT);
$recordId = Filter::filterVar($request->request->get('record_id'), FILTER_SANITIZE_SPECIAL_CHARS);
$recordLang = Filter::filterVar($request->request->get('record_lang'), FILTER_SANITIZE_SPECIAL_CHARS);
$csrfToken = Filter::filterVar($request->query->get('csrf'), FILTER_SANITIZE_SPECIAL_CHARS);

switch ($ajaxAction) {
    case 'delete':
        $deleteData = json_decode(file_get_contents('php://input', true));
        try {
            if (!Token::getInstance()->verifyToken('delete-attachment', $deleteData->csrf)) {
                $response->setStatusCode(Response::HTTP_UNAUTHORIZED);
                $response->setData(['error' => Translation::get('err_NotAuth')]);
                $response->send();
                exit();
            }

            $attachment = AttachmentFactory::create($deleteData->attId);
            if ($attachment->delete()) {
                $response->setStatusCode(Response::HTTP_OK);
                $result = ['success' => Translation::get('msgAttachmentsDeleted')];
            } else {
                $response->setStatusCode(Response::HTTP_BAD_REQUEST);
                $result = ['error' => Translation::get('ad_att_delfail')];
            }
        } catch (AttachmentException $e) {
            $response->setStatusCode(Response::HTTP_INTERNAL_SERVER_ERROR);
            $result = ['error' => $e->getMessage()];
        }
        $response->setData($result);
        $response->send();
        break;

    case 'upload':
        if (!isset($_FILES['filesToUpload'])) {
            $response->setStatusCode(Response::HTTP_BAD_REQUEST);
            return;
        }

        $files = AttachmentFactory::rearrangeUploadedFiles($_FILES['filesToUpload']);
        $uploadedFiles = [];

        foreach ($files as $file) {
            if (
                is_uploaded_file($file['tmp_name']) &&
                !($file['size'] > $faqConfig->get('records.maxAttachmentSize')) &&
                $file['type'] !== "text/html"
            ) {
                $attachment = AttachmentFactory::create();
                $attachment->setRecordId($recordId);
                $attachment->setRecordLang($recordLang);
                try {
                    if (!$attachment->save($file['tmp_name'], $file['name'])) {
                        throw new AttachmentException();
                    }
                } catch (AttachmentException $e) {
                    $attachment->delete();
                }
                $uploadedFiles[] = [
                    'attachmentId' => $attachment->getId(),
                    'fileName' => $attachment->getFilename(),
                    'faqId' => $recordId,
                    'faqLanguage' => $recordLang
                ];
            } else {
                $response->setStatusCode(Response::HTTP_BAD_REQUEST);
                $response->setData('The image is too large.');
                $response->send();
                return;
            }
        }

        $response->setStatusCode(Response::HTTP_OK);
        $response->setData($uploadedFiles);
        $response->send();
        break;
}

// -x-
<?php

/**
 * Private phpMyFAQ Admin API: handling of REST category calls.
 *
 * This Source Code Form is subject to the terms of the Mozilla Public License,
 * v. 2.0. If a copy of the MPL was not distributed with this file, You can
 * obtain one at https://mozilla.org/MPL/2.0/.
 *
 * @package   phpMyFAQ
 * @author    Thorsten Rinne <thorsten@phpmyfaq.de>
 * @copyright 2012-2023 phpMyFAQ Team
 * @license   https://www.mozilla.org/MPL/2.0/ Mozilla Public License Version 2.0
 * @link      https://www.phpmyfaq.de
 * @since     2012-12-26
 */

use phpMyFAQ\Category;
use phpMyFAQ\Category\CategoryOrder;
use phpMyFAQ\Category\CategoryPermission;
use phpMyFAQ\Filter;
use phpMyFAQ\Session\Token;
use phpMyFAQ\Translation;
use Symfony\Component\HttpFoundation\JsonResponse;
use Symfony\Component\HttpFoundation\Request;
use Symfony\Component\HttpFoundation\Response;

if (!defined('IS_VALID_PHPMYFAQ')) {
    http_response_code(400);
    exit();
}

//
// Create Request & Response
//
$response = new JsonResponse();
$request = Request::createFromGlobals();

$ajaxAction = Filter::filterVar($request->query->get('ajaxaction'), FILTER_SANITIZE_SPECIAL_CHARS);
$csrfToken = Filter::filterVar($request->query->get('csrf'), FILTER_SANITIZE_SPECIAL_CHARS);

switch ($ajaxAction) {
    case 'getpermissions':
        $categoryPermission = new CategoryPermission($faqConfig);
        $ajaxData = Filter::filterInputArray(
            INPUT_GET,
            [
                'categories' => [
                    'filter' => FILTER_SANITIZE_SPECIAL_CHARS,
                    'flags' => FILTER_REQUIRE_SCALAR,
                ],
            ]
        );

        if (empty($ajaxData['categories'])) {
            $categories = [-1]; // Access for all users and groups
        } else {
            $categories = explode(',', (int)$ajaxData['categories']);
        }

        $response->setData(
            [
                'user' => $categoryPermission->get(CategoryPermission::USER, $categories),
                'group' => $categoryPermission->get(CategoryPermission::GROUP, $categories)
            ]
        );
        $response->send();
        break;

    case 'update-order':
        $postData = json_decode(file_get_contents('php://input', true));

        if (!Token::getInstance()->verifyToken('category', $postData->csrf)) {
            $response->setStatusCode(Response::HTTP_UNAUTHORIZED);
            $response->setData(['error' => Translation::get('err_NotAuth')]);
            $response->send();
            exit();
        }

        $category = new Category($faqConfig, [], false);
        $category->setUser($currentAdminUser);
        $category->setGroups($currentAdminGroups);

        $categoryOrder = new CategoryOrder($faqConfig);

        /**
         * Callback function for array_filter()
         * @param $element
         * @return bool
         */
        function filterElement($element): bool
        {
            return is_numeric($element) ?? (int)$element;
        }

        $sortedData = array_filter($postData->order, 'filterElement');

        $order = 1;
        foreach ($sortedData as $categoryId) {
            $currentPosition = $categoryOrder->getPositionById((int) $categoryId);

            if (!$currentPosition) {
                $categoryOrder->setPositionById((int) $categoryId, $order);
            } else {
                $categoryOrder->updatePositionById((int) $categoryId, $order);
            }
            $order++;
        }

        $response->setData(
            ['success' => Translation::get('ad_categ_save_order')]
        );
        $response->send();
        break;
}

// -x-

<?php

/**
 * Private phpMyFAQ Admin API: deletes comments with the given id.
 *
 * This Source Code Form is subject to the terms of the Mozilla Public License,
 * v. 2.0. If a copy of the MPL was not distributed with this file, You can
 * obtain one at https://mozilla.org/MPL/2.0/.
 *
 * @package   phpMyFAQ
 * @author    Thorsten Rinne <thorsten@phpmyfaq.de>
 * @copyright 2009-2023 phpMyFAQ Team
 * @license   https://www.mozilla.org/MPL/2.0/ Mozilla Public License Version 2.0
 * @link      https://www.phpmyfaq.de
 * @since     2009-03-20
 */

use phpMyFAQ\Comments;
use phpMyFAQ\Session\Token;
use phpMyFAQ\Translation;
use Symfony\Component\HttpFoundation\JsonResponse;
use Symfony\Component\HttpFoundation\Request;
use Symfony\Component\HttpFoundation\Response;

if (!defined('IS_VALID_PHPMYFAQ')) {
    http_response_code(400);
    exit();
}

//
// Create Request & Response
//
$response = new JsonResponse();
$request = Request::createFromGlobals();

$deleteData = json_decode(file_get_contents('php://input', true));

if ('delete' === $deleteData->data->ajaxaction && $user->perm->hasPermission($user->getUserId(), 'delcomment')) {
    if (!Token::getInstance()->verifyToken('delete-comment', $deleteData->data->{'pmf-csrf-token'})) {
        $response->setStatusCode(Response::HTTP_UNAUTHORIZED);
        $response->setData(['error' => Translation::get('err_NotAuth')]);
        $response->send();
        exit();
    }

    $comment = new Comments($faqConfig);
    $success = false;

    $commentIds = $deleteData->data->{'comments[]'} ?? [];

    if (!is_null($commentIds)) {
        if (!is_array($commentIds)) {
            $commentIds = [$commentIds];
        }
        foreach ($commentIds as $commentId) {
            $success = $comment->delete($deleteData->type, $commentId);
        }

        $response->setStatusCode(Response::HTTP_OK);
        $response->setData(['success' => $success]);
    } else {
        $response->setStatusCode(Response::HTTP_BAD_REQUEST);
        $response->setData(['error' => false]);
    }
    $response->send();
}

// -x-

<?php

/**
 * Private phpMyFAQ Admin API: lists the complete configuration items as text/html.
 *
 * This Source Code Form is subject to the terms of the Mozilla Public License,
 * v. 2.0. If a copy of the MPL was not distributed with this file, You can
 * obtain one at https://mozilla.org/MPL/2.0/.
 *
 * @package   phpMyFAQ
 * @author    Thorsten Rinne <thorsten@phpmyfaq.de>
 * @author    Thomas Zeithaml <tom@annatom.de>
 * @copyright 2005-2023 phpMyFAQ Team
 * @license   https://www.mozilla.org/MPL/2.0/ Mozilla Public License Version 2.0
 * @link      https://www.phpmyfaq.de
 * @since     2005-12-26
 */

use Abraham\TwitterOAuth\TwitterOAuth;
use phpMyFAQ\Configuration;
use phpMyFAQ\Filter;
use phpMyFAQ\Helper\AdministrationHelper;
use phpMyFAQ\Helper\LanguageHelper;
use phpMyFAQ\Helper\PermissionHelper;
use phpMyFAQ\Strings;
use phpMyFAQ\System;
use phpMyFAQ\Translation;
use phpMyFAQ\Utils;
use Symfony\Component\HttpFoundation\Request;

if (!defined('IS_VALID_PHPMYFAQ')) {
    http_response_code(400);
    exit();
}

if (!empty($_SESSION['access_token'])) {
    $connection = new TwitterOAuth(
        $faqConfig->get('socialnetworks.twitterConsumerKey'),
        $faqConfig->get('socialnetworks.twitterConsumerSecret'),
        $_SESSION['access_token']['oauth_token'],
        $_SESSION['access_token']['oauth_token_secret']
    );

    $content = $connection->get('account/verify_credentials');
}

$request = Request::createFromGlobals();
$configMode = Filter::filterVar($request->query->get('conf'), FILTER_SANITIZE_SPECIAL_CHARS, 'main');

/**
 * @param mixed  $key
 * @param string $type
 */
function renderInputForm(mixed $key, string $type): void
{
    $faqConfig = Configuration::getConfigurationInstance();

    switch ($type) {
        case 'area':
            printf(
                '<textarea name="edit[%s]" rows="4" class="form-control">%s</textarea>',
                $key,
                str_replace('<', '&lt;', str_replace('>', '&gt;', $faqConfig->get($key)))
            );
            printf("</div>\n");
            break;

        case 'input':
            if (
                '' === $faqConfig->get($key) && 'socialnetworks.twitterAccessTokenKey' == $key &&
                isset($_SESSION['access_token'])
            ) {
                $value = $_SESSION['access_token']['oauth_token'];
            } elseif (
                '' === $faqConfig->get($key) && 'socialnetworks.twitterAccessTokenSecret' == $key &&
                isset($_SESSION['access_token'])
            ) {
                $value = $_SESSION['access_token']['oauth_token_secret'];
            } else {
                $value = str_replace('"', '&quot;', $faqConfig->get($key) ?? '');
            }
            echo '<div class="input-group">';

            switch ($key) {
                case 'main.administrationMail':
                    $type = 'email';
                    break;
                case 'main.referenceURL':
                case 'main.privacyURL':
                    $type = 'url';
                    break;
                default:
                    $type = 'text';
                    break;
            }

            printf(
                '<input class="form-control" type="%s" name="edit[%s]" id="edit[%s]" value="%s" step="1" min="0">',
                is_numeric($value) ? 'number' : $type,
                $key,
                $key,
                Strings::htmlentities($value)
            );

            if ('api.apiClientToken' === $key) {
                echo '<div class="input-group-append">';
                echo '<button class="btn btn-dark" id="pmf-generate-api-token" type="button" onclick="generateApiToken()">Generate API Client Token</button>';
                echo '</div>';
                ?>
                <script>
                  try {
                    const generateUUID = () => {
                      let date = new Date().getTime();

                      if (window.performance && typeof window.performance.now === 'function') {
                        date += performance.now();
                      }

                      return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, (char) => {
                        const random = (date + Math.random() * 16) % 16 | 0;
                        date = Math.floor(date / 16);
                        return (char === 'x' ? random : (random & 0x3 | 0x8)).toString(16);
                      });
                    }

                    const buttonGenerateApiToken = document.getElementById('pmf-generate-api-token');
                    const inputConfigurationApiToken = document.getElementById('edit[api.apiClientToken]');

                    if (buttonGenerateApiToken) {
                      if (inputConfigurationApiToken.value !== '') {
                        buttonGenerateApiToken.disabled = true;
                      }
                      buttonGenerateApiToken.addEventListener('click', (event) => {
                        event.preventDefault();
                        inputConfigurationApiToken.value = generateUUID();
                      });
                    }
                  } catch (e) {
                    // do nothing
                  }
                </script>
                <?php
            }
            echo '</div></div>';
            break;

        case 'password':
            printf(
                '<input class="form-control" type="password" autocomplete="off" name="edit[%s]" value="%s">',
                $key,
                Strings::htmlentities($faqConfig->get($key))
            );
            echo "</div>\n";
            break;

        case 'select':
            printf('<select name="edit[%s]" class="form-select">', $key);

            switch ($key) {
                case 'main.language':
                    $languages = LanguageHelper::getAvailableLanguages();
                    if (count($languages) > 0) {
                        echo LanguageHelper::renderLanguageOptions(
                            str_replace(
                                [ 'language_', '.php', ],
                                '',
                                $faqConfig->get('main.language')
                            ),
                            false,
                            true
                        );
                    } else {
                        echo '<option value="language_en.php">English</option>';
                    }
                    break;

                case 'records.orderby':
                    echo AdministrationHelper::sortingOptions($faqConfig->get($key));
                    break;

                case 'records.sortby':
                    printf(
                        '<option value="DESC" %s>%s</option>',
                        ('DESC' == $faqConfig->get($key)) ? 'selected' : '',
                        Translation::get('ad_conf_desc')
                    );
                    printf(
                        '<option value="ASC" %s>%s</option>',
                        ('ASC' == $faqConfig->get($key)) ? 'selected' : '',
                        Translation::get('ad_conf_asc')
                    );
                    break;

                case 'security.permLevel':
                    echo PermissionHelper::permOptions($faqConfig->get($key));
                    break;

                case 'main.templateSet':
                    $faqSystem = new System();
                    $templates = $faqSystem->getAvailableTemplates();

                    foreach ($templates as $template => $selected) {
                        printf(
                            '<option%s>%s</option>',
                            ($selected === true ? ' selected' : ''),
                            $template
                        );
                    }
                    break;

                case 'records.attachmentsStorageType':
                    foreach (Translation::get('att_storage_type') as $i => $item) {
                        $selected = (int)$faqConfig->get($key) === $i ? ' selected' : '';
                        printf('<option value="%d"%s>%s</option>', $i, $selected, $item);
                    }
                    break;

                case 'records.orderingPopularFaqs':
                    printf(
                        '<option value="visits"%s>%s</option>',
                        ('visits' === $faqConfig->get($key)) ? ' selected' : '',
                        Translation::get('records.orderingPopularFaqs.visits')
                    );
                    printf(
                        '<option value="voting"%s>%s</option>',
                        ('voting' === $faqConfig->get($key)) ? ' selected' : '',
                        Translation::get('records.orderingPopularFaqs.voting')
                    );
                    break;

                case 'search.relevance':
                    printf(
                        '<option value="thema,content,keywords"%s>%s</option>',
                        ('thema,content,keywords' == $faqConfig->get($key)) ? ' selected' : '',
                        Translation::get('search.relevance.thema-content-keywords')
                    );
                    printf(
                        '<option value="thema,keywords,content"%s>%s</option>',
                        (
                            'thema,keywords,content' == $faqConfig->get($key)) ? ' selected' : '',
                        Translation::get('search.relevance.thema-keywords-content')
                    );
                    printf(
                        '<option value="content,thema,keywords"%s>%s</option>',
                        ('content,thema,keywords' == $faqConfig->get($key)) ? ' selected' : '',
                        Translation::get('search.relevance.content-thema-keywords')
                    );
                    printf(
                        '<option value="content,keywords,thema"%s>%s</option>',
                        ('content,keywords,thema' == $faqConfig->get($key)) ? ' selected' : '',
                        Translation::get('search.relevance.content-keywords-thema')
                    );
                    printf(
                        '<option value="keywords,content,thema"%s>%s</option>',
                        ('keywords,content,thema' == $faqConfig->get($key)) ? ' selected' : '',
                        Translation::get('search.relevance.keywords-content-thema')
                    );
                    printf(
                        '<option value="keywords,thema,content"%s>%s</option>',
                        ('keywords,thema,content' == $faqConfig->get($key)) ? ' selected' : '',
                        Translation::get('search.relevance.keywords-thema-content')
                    );
                    break;

                case 'seo.metaTagsHome':
                case 'seo.metaTagsFaqs':
                case 'seo.metaTagsCategories':
                case 'seo.metaTagsPages':
                case 'seo.metaTagsAdmin':
                    $adminHelper = new AdministrationHelper();
                    echo $adminHelper->renderMetaRobotsDropdown($faqConfig->get($key));
                    break;
            }

            echo "</select>\n</div>\n";
            break;

        case 'checkbox':
            printf(
                '<div class="form-check"><input class="form-check-input" type="checkbox" name="edit[%s]" value="true"',
                $key
            );
            if ($faqConfig->get($key)) {
                echo ' checked';
            }
            if ('ldap.ldapSupport' === $key && !extension_loaded('ldap')) {
                echo ' disabled';
            }
            if ('security.useSslForLogins' === $key && !Request::createFromGlobals()->isSecure()) {
                echo ' disabled';
            }
            if ('security.useSslOnly' === $key && !Request::createFromGlobals()->isSecure()) {
                echo ' disabled';
            }
            if ('security.ssoSupport' === $key && !Request::createFromGlobals()->server->get('REMOTE_USER')) {
                echo ' disabled';
            }
            echo '></div></div>';
            break;

        case 'print':
            printf(
                '<input type="text" readonly name="edit[%s]" class="form-control-plaintext" value="%s"></div>',
                $key,
                str_replace('"', '&quot;', $faqConfig->get($key))
            );
            break;

        case 'button':
            printf(
                '<button type="button" class="btn btn-primary" id="btn-phpmyfaq-%s" onclick="handleSendTestMail()">%s</button></div>',
                str_replace('.', '-', $key),
                Translation::get($key)
            );
            break;
    }
}

header('Content-type: text/html; charset=utf-8');

Utils::moveToTop($LANG_CONF, 'main.maintenanceMode');

foreach ($LANG_CONF as $key => $value) {
    if (strpos($key, $configMode) === 0) {
        if ('socialnetworks.twitterConsumerKey' == $key) {
            echo '<div class="row mb-2"><label class="col-form-label col-lg-3"></label>';
            echo '<div class="col-lg-9">';
            if (
                '' == $faqConfig->get('socialnetworks.twitterConsumerKey') ||
                '' == $faqConfig->get('socialnetworks.twitterConsumerSecret')
            ) {
                echo '<a target="_blank" href="https://dev.twitter.com/apps/new">Create Twitter App for your FAQ</a>';
                echo "<br>\n";
                echo 'Your Callback URL is: ' . $faqConfig->getDefaultUrl() . 'services/twitter/callback.php';
            }

            if (!isset($content)) {
                echo '<br><a target="_blank" href="../../services/twitter/redirect.php">';
                echo '<img src="../../assets/img/twitter.signin.png" alt="Sign in with Twitter"/></a>';
            } else {
                echo $content->screen_name . "<br>\n";
                echo "<img alt=\"Twitter profile\" src='" . $content->profile_image_url_https . "'><br>\n";
                echo 'Follower: ' . $content->followers_count . "<br>\n";
                echo 'Status Count: ' . $content->statuses_count . "<br>\n";
                echo 'Status: ' . $content->status->text;
            }
            echo '</div></div>';
        }

        printf(
            '<div class="row mb-2"><label class="col-lg-3 col-form-label %s">',
            $value[0] === 'checkbox' || $value[0] === 'radio' ? 'pt-0' : ''
        );

        switch ($key) {
            case 'records.maxAttachmentSize':
                printf($value[1], ini_get('upload_max_filesize'));
                break;
            case 'main.dateFormat':
                printf(
                    '<a target="_blank" href="https://www.php.net/manual/%s/function.date.php">%s</a>',
                    $faqLangCode,
                    $value[1]
                );
                break;
            default:
                echo $value[1];
                break;
        }
        ?>
      </label>
      <div class="col-lg-9">
          <?php renderInputForm($key, $value[0]); ?>
      </div>
        <?php
    }
}

// -x-

<?php

/**
 * Private phpMyFAQ Admin API: handling of REST configuration calls.
 *
 * This Source Code Form is subject to the terms of the Mozilla Public License,
 * v. 2.0. If a copy of the MPL was not distributed with this file, You can
 * obtain one at https://mozilla.org/MPL/2.0/.
 *
 * @package   phpMyFAQ
 * @author    Anatoliy Belsky <anatoliy.belsky@mayflower.de>
 * @author    Thorsten Rinne <thorsten@phpmyfaq.de>
 * @copyright 2009-2023 phpMyFAQ Team
 * @license   https://www.mozilla.org/MPL/2.0/ Mozilla Public License Version 2.0
 * @link      https://www.phpmyfaq.de
 * @since     2009-04-01
 */

use phpMyFAQ\Configuration\DatabaseConfiguration;
use phpMyFAQ\Core\Exception;
use phpMyFAQ\Database;
use phpMyFAQ\Entity\InstanceEntity;
use phpMyFAQ\Entity\TemplateMetaDataEntity;
use phpMyFAQ\Filter;
use phpMyFAQ\Instance;
use phpMyFAQ\Instance\Client;
use phpMyFAQ\Instance\Setup;
use phpMyFAQ\Language;
use phpMyFAQ\Mail;
use phpMyFAQ\Session\Token;
use phpMyFAQ\Template\TemplateMetaData;
use phpMyFAQ\StopWords;
use phpMyFAQ\Translation;
use phpMyFAQ\User;
use Symfony\Component\HttpFoundation\JsonResponse;
use Symfony\Component\HttpFoundation\Request;
use Symfony\Component\HttpFoundation\Response;
use Symfony\Component\Mailer\Exception\TransportExceptionInterface;

if (!defined('IS_VALID_PHPMYFAQ')) {
    http_response_code(400);
    exit();
}

//
// Create Request & Response
//
$response = new JsonResponse();
$request = Request::createFromGlobals();

$ajaxAction = Filter::filterVar($request->query->get('ajaxaction'), FILTER_SANITIZE_SPECIAL_CHARS);
$instanceId = Filter::filterVar($request->query->get('instanceId'), FILTER_VALIDATE_INT);
$stopwordId = Filter::filterVar($request->query->get('stopword_id'), FILTER_VALIDATE_INT);
$stopword = Filter::filterVar($request->query->get('stopword'), FILTER_SANITIZE_SPECIAL_CHARS);
$stopwordsLang = Filter::filterVar($request->query->get('stopwords_lang'), FILTER_SANITIZE_SPECIAL_CHARS);
$csrfToken = Filter::filterVar($request->query->get('csrf'), FILTER_SANITIZE_SPECIAL_CHARS);

$stopWords = new StopWords($faqConfig);

switch ($ajaxAction) {
    case 'add-instance':
        $postData = json_decode(file_get_contents('php://input', true));

        if (!Token::getInstance()->verifyToken('add-instance', $postData->csrf)) {
            $response->setStatusCode(Response::HTTP_UNAUTHORIZED);
            $response->setData(['error' => Translation::get('err_NotAuth')]);
            $response->send();
            exit();
        }

        $url = Filter::filterVar($postData->url, FILTER_SANITIZE_SPECIAL_CHARS);
        $instance = Filter::filterVar($postData->instance, FILTER_SANITIZE_SPECIAL_CHARS);
        $comment = Filter::filterVar($postData->comment, FILTER_SANITIZE_SPECIAL_CHARS);
        $email = Filter::filterVar($postData->email, FILTER_VALIDATE_EMAIL);
        $admin = Filter::filterVar($postData->admin, FILTER_SANITIZE_SPECIAL_CHARS);
        $password = Filter::filterVar($postData->password, FILTER_SANITIZE_SPECIAL_CHARS);

        if (empty($url) || empty($instance) || empty($comment) || empty($email) || empty($admin) || empty($password)) {
            $response->setStatusCode(Response::HTTP_BAD_REQUEST);
            $response->setData(['error' => 'Cannot create instance.']);
            $response->send();
            exit(1);
        }

        $url = 'https://' . $url . '.' . $_SERVER['SERVER_NAME'];
        if (!Filter::filterVar($url, FILTER_VALIDATE_URL)) {
            $response->setStatusCode(Response::HTTP_BAD_REQUEST);
            $response->setData(['error' => 'Cannot create instance: wrong URL']);
            $response->send();
            exit(1);
        }

        $data = new InstanceEntity();
        $data
            ->setUrl($url)
            ->setInstance($instance)
            ->setComment($comment);

        $faqInstance = new Instance($faqConfig);
        $instanceId = $faqInstance->addInstance($data);

        $faqInstanceClient = new Client($faqConfig);
        $faqInstanceClient->createClient($faqInstance);

        $urlParts = parse_url($data->getUrl());
        $hostname = $urlParts['host'];

        if ($faqInstanceClient->createClientFolder($hostname)) {
            $clientDir = PMF_ROOT_DIR . '/multisite/' . $hostname;
            $clientSetup = new Setup();
            $clientSetup->setRootDir($clientDir);

            try {
                $faqInstanceClient->copyConstantsFile($clientDir . '/constants.php');
            } catch (Exception $e) {
                $response->setStatusCode(Response::HTTP_BAD_REQUEST);
                $response->setData(['error' => $e->getMessage()]);
                $response->send();
                exit(1);
            }

            $dbConfig = new DatabaseConfiguration(PMF_CONFIG_DIR . '/database.php');
            $dbSetup = [
                'dbServer' => $dbConfig->getServer(),
                'dbPort' => $dbConfig->getPort(),
                'dbUser' => $dbConfig->getUser(),
                'dbPassword' => $dbConfig->getPassword(),
                'dbDatabaseName' => $dbConfig->getDatabase(),
                'dbPrefix' => substr($hostname, 0, strpos($hostname, '.')),
                'dbType' => $dbConfig->getType()
            ];
            $clientSetup->createDatabaseFile($dbSetup, '');

            $faqInstanceClient->setClientUrl('https://' . $hostname);
            $faqInstanceClient->createClientTables($dbSetup['dbPrefix']);

            Database::setTablePrefix($dbSetup['dbPrefix']);

            // add an admin account and rights
            $instanceAdmin = new User($faqConfig);
            $instanceAdmin->createUser($admin, $password, '', 1);
            $instanceAdmin->setStatus('protected');
            $instanceAdminData = [
                'display_name' => '',
                'email' => $email,
            ];
            $instanceAdmin->setUserData($instanceAdminData);

            // Add an anonymous user account
            try {
                $clientSetup->createAnonymousUser($faqConfig);
            } catch (Exception $e) {
                $response->setStatusCode(Response::HTTP_BAD_REQUEST);
                $payload = ['error' => $e->getMessage()];
            }

            Database::setTablePrefix($dbConfig->getPrefix());
        } else {
            $faqInstance->removeInstance($instanceId);
            $response->setStatusCode(Response::HTTP_BAD_REQUEST);
            $payload = ['error' => 'Cannot create instance.'];
        }
        if (0 !== $instanceId) {
            $response->setStatusCode(Response::HTTP_OK);
            $payload = ['added' => $instanceId, 'url' => $data->getUrl()];
        } else {
            $response->setStatusCode(Response::HTTP_BAD_REQUEST);
            $payload = ['error' => $instanceId];
        }
        $response->setData($payload);
        $response->send();
        break;

    case 'delete-instance':
        $postData = json_decode(file_get_contents('php://input', true));

        if (!Token::getInstance()->verifyToken('delete-instance', $postData->csrf)) {
            $response->setStatusCode(Response::HTTP_UNAUTHORIZED);
            $response->setData(['error' => Translation::get('err_NotAuth')]);
            $response->send();
            exit();
        }

        $instanceId = Filter::filterVar($postData->instanceId, FILTER_SANITIZE_SPECIAL_CHARS);

        if (null !== $instanceId) {
            $client = new Client($faqConfig);
            $clientData = $client->getInstanceById($instanceId);
            if (
                1 !== $instanceId &&
                $client->deleteClientFolder($clientData->url) &&
                $client->removeInstance($instanceId)
            ) {
                $response->setStatusCode(Response::HTTP_OK);
                $payload = ['deleted' => $instanceId];
            } else {
                $response->setStatusCode(Response::HTTP_BAD_REQUEST);
                $payload = ['error' => $instanceId];
            }
            $response->setData($payload);
            $response->send();
        }
        break;

    case 'load_stop_words_by_lang':
        if (Language::isASupportedLanguage($stopwordsLang)) {
            $stopWordsList = $stopWords->getByLang($stopwordsLang);
            $response->setStatusCode(Response::HTTP_OK);
            $response->setData($stopWordsList);
            $response->send();
        }
        break;

    case 'delete_stop_word':
        $deleteData = json_decode(file_get_contents('php://input', true));

        $stopWordId = Filter::filterVar($deleteData->stopWordId, FILTER_VALIDATE_INT);
        $stopWordsLang = Filter::filterVar($deleteData->stopWordsLang, FILTER_SANITIZE_SPECIAL_CHARS);

        if (!Token::getInstance()->verifyToken('stopwords', $deleteData->csrf)) {
            $response->setStatusCode(Response::HTTP_UNAUTHORIZED);
            $response->setData(['error' => Translation::get('err_NotAuth')]);
            $response->send();
            exit();
        }

        if (null != $stopWordId && Language::isASupportedLanguage($stopWordsLang)) {
            $stopWords
                ->setLanguage($stopWordsLang)
                ->remove((int)$stopWordId);
            $response->setStatusCode(Response::HTTP_OK);
            $response->setData(['deleted' => $stopWordId ]);
            $response->send();
        }
        break;

    case 'save_stop_word':
        $postData = json_decode(file_get_contents('php://input', true));

        $stopWordId = Filter::filterVar($postData->stopWordId, FILTER_VALIDATE_INT);
        $stopWordsLang = Filter::filterVar($postData->stopWordsLang, FILTER_SANITIZE_SPECIAL_CHARS);
        $stopWord = Filter::filterVar($postData->stopWord, FILTER_SANITIZE_SPECIAL_CHARS);

        if (!Token::getInstance()->verifyToken('stopwords', $postData->csrf)) {
            $response->setStatusCode(Response::HTTP_UNAUTHORIZED);
            $response->setData(['error' => Translation::get('err_NotAuth')]);
            $response->send();
            exit();
        }

        if (null != $stopWord && Language::isASupportedLanguage($stopWordsLang)) {
            $stopWords->setLanguage($stopWordsLang);

            if (null !== $stopWordId && -1 < $stopWordId) {
                $stopWords->update((int)$stopWordId, $stopWord);
                $response->setStatusCode(Response::HTTP_OK);
                $response->setData(['updated' => $stopWordId ]);
            } elseif (!$stopWords->match($stopWord)) {
                $stopWordId = $stopWords->add($stopWord);
                $response->setStatusCode(Response::HTTP_OK);
                $response->setData(['added' => $stopWordId ]);
            }
            $response->send();
        }
        break;

    case 'add-template-metadata':
        $postData = json_decode(file_get_contents('php://input', true));

        if (!Token::getInstance()->verifyToken('add-metadata', $postData->csrf)) {
            $response->setStatusCode(Response::HTTP_UNAUTHORIZED);
            $response->setData(['error' => Translation::get('err_NotAuth')]);
            $response->send();
            exit();
        }

        $meta = new TemplateMetaData($faqConfig);
        $entity = new TemplateMetaDataEntity();

        $entity
            ->setPageId(Filter::filterVar($postData->pageId, FILTER_SANITIZE_SPECIAL_CHARS))
            ->setType(Filter::filterVar($postData->type, FILTER_SANITIZE_SPECIAL_CHARS))
            ->setContent(Filter::filterVar($postData->content, FILTER_SANITIZE_SPECIAL_CHARS));

        $metaId = $meta->add($entity);

        if (0 !== $metaId) {
            $payload = ['added' => $metaId];
        } else {
            $response->setStatusCode(Response::HTTP_BAD_REQUEST);
            $payload = ['error' => $metaId];
        }

        $response->setData($payload);
        $response->send();
        break;

    case 'delete-template-metadata':
        $json = file_get_contents('php://input', true);
        $deleteData = json_decode($json);

        if (!Token::getInstance()->verifyToken('delete-meta-data', $deleteData->csrf)) {
            $response->setStatusCode(Response::HTTP_UNAUTHORIZED);
            $response->setData(['error' => Translation::get('err_NotAuth')]);
            $response->send();
            exit();
        }

        $meta = new TemplateMetaData($faqConfig);
        $metaId = Filter::filterVar($deleteData->metaId, FILTER_SANITIZE_SPECIAL_CHARS);

        if ($meta->delete((int)$metaId)) {
            $payload = ['deleted' => $metaId];
        } else {
            $response->setStatusCode(Response::HTTP_BAD_REQUEST);
            $payload = ['error' => $metaId];
        }

        $response->setData($payload);
        $response->send();
        break;

    case 'send-test-mail':
        $json = file_get_contents('php://input', true);
        $postData = json_decode($json);

        if (!Token::getInstance()->verifyToken('configuration', $postData->csrf)) {
            $response->setStatusCode(Response::HTTP_UNAUTHORIZED);
            $response->setData(['error' => Translation::get('err_NotAuth')]);
            $response->send();
            exit();
        }

        try {
            $mailer = new Mail($faqConfig);
            $mailer->setReplyTo($faqConfig->getAdminEmail());
            $mailer->addTo($faqConfig->getAdminEmail());
            $mailer->subject = $faqConfig->getTitle() . ': Mail test successful.';
            $mailer->message = 'It works on my machine. 🚀';
            $result = $mailer->send();

            $response->setStatusCode(Response::HTTP_OK);
            $response->setData(['success' => $result]);
        } catch (Exception | TransportExceptionInterface $e) {
            $response->setStatusCode(Response::HTTP_BAD_REQUEST);
            $response->setData(['error' => $e->getMessage()]);
        }

        $response->send();
        break;
}

// -x-

<?php

/**
 * Private phpMyFAQ Admin API: handling of REST calls for the dashboard
 *
 * This Source Code Form is subject to the terms of the Mozilla Public License,
 * v. 2.0. If a copy of the MPL was not distributed with this file, You can
 * obtain one at https://mozilla.org/MPL/2.0/.
 *
 * @package   phpMyFAQ
 * @author    Thorsten Rinne <thorsten@phpmyfaq.de>
 * @copyright 2020-2023 phpMyFAQ Team
 * @license   https://www.mozilla.org/MPL/2.0/ Mozilla Public License Version 2.0
 * @link      https://www.phpmyfaq.de
 * @since     2020-10-24
 */

use phpMyFAQ\Api;
use phpMyFAQ\Configuration;
use phpMyFAQ\Filter;
use phpMyFAQ\Session;
use phpMyFAQ\Translation;
use Symfony\Component\HttpFoundation\JsonResponse;
use Symfony\Component\HttpFoundation\Request;
use Symfony\Component\HttpFoundation\Response;
use Symfony\Contracts\HttpClient\Exception\DecodingExceptionInterface;
use Symfony\Contracts\HttpClient\Exception\TransportExceptionInterface;

if (!defined('IS_VALID_PHPMYFAQ')) {
    http_response_code(400);
    exit();
}

//
// Create Request & Response
//
$response = new JsonResponse();
$request = Request::createFromGlobals();

$faqConfig = Configuration::getConfigurationInstance();

$ajaxAction = Filter::filterVar($request->query->get('ajaxaction'), FILTER_SANITIZE_SPECIAL_CHARS);

switch ($ajaxAction) {
    case 'user-visits-last-30-days':
        if ($faqConfig->get('main.enableUserTracking')) {
            $session = new Session($faqConfig);
            $response->setStatusCode(Response::HTTP_OK);
            $response->setData($session->getLast30DaysVisits());
        }
        break;

    case 'version':
        $api = new Api($faqConfig);
        try {
            $versions = $api->getVersions();
            $response->setStatusCode(Response::HTTP_OK);
            if (-1 === version_compare($versions['installed'], $versions['current'])) {
                $response->setData(
                    ['info' => Translation::get('ad_you_should_update')]
                );
            } else {
                $response->setData(
                    ['success' => Translation::get('ad_xmlrpc_latest') . ': phpMyFAQ ' . $versions['current']]
                );
            }
        } catch (DecodingExceptionInterface | TransportExceptionInterface | Exception $e) {
            $response->setStatusCode(Response::HTTP_BAD_GATEWAY);
            $response->setData(['error' => $e->getMessage()]);
        }
        break;
}

$response->send();

// -x-

<?php

/**
 * Private phpMyFAQ Admin API: Elasticsearch configuration backend
 *
 * This Source Code Form is subject to the terms of the Mozilla Public License,
 * v. 2.0. If a copy of the MPL was not distributed with this file, You can
 * obtain one at https://mozilla.org/MPL/2.0/.
 *
 * @package   phpMyFAQ
 * @author    Thorsten Rinne <thorsten@phpmyfaq.de>
 * @copyright 2015-2023 phpMyFAQ Team
 * @license   https://www.mozilla.org/MPL/2.0/ Mozilla Public License Version 2.0
 * @link      https://www.phpmyfaq.de
 * @since     2015-12-26
 */

use Elastic\Elasticsearch\Exception\ClientResponseException;
use Elastic\Elasticsearch\Exception\ServerResponseException;
use phpMyFAQ\Configuration;
use phpMyFAQ\Faq;
use phpMyFAQ\Filter;
use phpMyFAQ\Instance\Elasticsearch;
use phpMyFAQ\Translation;
use Symfony\Component\HttpFoundation\JsonResponse;
use Symfony\Component\HttpFoundation\Request;
use Symfony\Component\HttpFoundation\Response;

if (!defined('IS_VALID_PHPMYFAQ')) {
    http_response_code(400);
    exit();
}

//
// Create Request & Response
//
$response = new JsonResponse();
$request = Request::createFromGlobals();

$faqConfig = Configuration::getConfigurationInstance();

$ajaxAction = Filter::filterVar($request->query->get('ajaxaction'), FILTER_SANITIZE_SPECIAL_CHARS);

$elasticsearch = new Elasticsearch($faqConfig);

$esConfigData = $faqConfig->getElasticsearchConfig();

$result = [];

switch ($ajaxAction) {
    case 'create':
        try {
            $esResult = $elasticsearch->createIndex();
            $response->setStatusCode(Response::HTTP_OK);
            $result = ['success' => Translation::get('ad_es_create_index_success')];
        } catch (Exception $e) {
            $response->setStatusCode(Response::HTTP_CONFLICT);
            $result = ['error' => $e->getMessage()];
        }
        break;

    case 'drop':
        try {
            $esResult = $elasticsearch->dropIndex();
            $response->setStatusCode(Response::HTTP_OK);
            $result = ['success' => Translation::get('ad_es_drop_index_success')];
        } catch (Exception $e) {
            $response->setStatusCode(Response::HTTP_BAD_REQUEST);
            $result = ['error' => $e->getMessage()];
        }
        break;

    case 'import':
        $faq = new Faq($faqConfig);
        $faq->getAllRecords();
        $bulkIndexResult = $elasticsearch->bulkIndex($faq->faqRecords);
        if (isset($bulkIndexResult['success'])) {
            $response->setStatusCode(Response::HTTP_OK);
            $result = ['success' => Translation::get('ad_es_create_import_success')];
        } else {
            $response->setStatusCode(Response::HTTP_BAD_REQUEST);
            $result = ['error' => $bulkIndexResult];
        }
        break;

    case 'stats':
        $indexName = $esConfigData->getIndex();
        try {
            $response->setStatusCode(Response::HTTP_OK);
            $result = [
                'index' => $indexName,
                'stats' => $faqConfig->getElasticsearch()->indices()->stats(['index' => $indexName])->asArray()
            ];
        } catch (ClientResponseException | ServerResponseException $e) {
            $response->setStatusCode(Response::HTTP_BAD_REQUEST);
            $result = ['error' => $e->getMessage()];
        }
        break;
}

$response->setData($result);
$response->send();

// -x-

<?php

/**
 * Private phpMyFAQ Admin API: handling of Ajax record calls.
 *
 * This Source Code Form is subject to the terms of the Mozilla Public License,
 * v. 2.0. If a copy of the MPL was not distributed with this file, You can
 * obtain one at https://mozilla.org/MPL/2.0/.
 *
 * @package   phpMyFAQ
 * @author    Anatoliy Belsky <anatoliy.belsky@mayflower.de>
 * @author    Thorsten Rinne <thorsten@phpmyfaq.de>
 * @copyright 2009-2023 phpMyFAQ Team
 * @license   https://www.mozilla.org/MPL/2.0/ Mozilla Public License Version 2.0
 * @link      https://www.phpmyfaq.de
 * @since     2009-03-31
 */

use phpMyFAQ\Attachment\AttachmentException;
use phpMyFAQ\Attachment\Filesystem\File\FileException;
use phpMyFAQ\Category;
use phpMyFAQ\Faq;
use phpMyFAQ\Faq\FaqPermission;
use phpMyFAQ\Filter;
use phpMyFAQ\Helper\SearchHelper;
use phpMyFAQ\Language;
use phpMyFAQ\AdminLog;
use phpMyFAQ\Question;
use phpMyFAQ\Search;
use phpMyFAQ\Search\SearchResultSet;
use phpMyFAQ\Session\Token;
use phpMyFAQ\Translation;
use Symfony\Component\HttpFoundation\JsonResponse;
use Symfony\Component\HttpFoundation\Request;
use Symfony\Component\HttpFoundation\Response;

if (!defined('IS_VALID_PHPMYFAQ')) {
    http_response_code(400);
    exit();
}

//
// Create Request & Response
//
$response = new JsonResponse();
$request = Request::createFromGlobals();

$ajaxAction = Filter::filterVar($request->query->get('ajaxaction'), FILTER_SANITIZE_SPECIAL_CHARS);
$csrfTokenPost = Filter::filterInput(INPUT_POST, 'csrf', FILTER_SANITIZE_SPECIAL_CHARS);
$csrfTokenGet = Filter::filterInput(INPUT_GET, 'csrf', FILTER_SANITIZE_SPECIAL_CHARS);

$csrfToken = (is_null($csrfTokenPost) ? $csrfTokenGet : $csrfTokenPost);

$items = isset($_GET['items']) && is_array($_GET['items']) ? $_GET['items'] : [];

if (!isset($items[0][2])) {
    $items[0][2] = 0;
}

switch ($ajaxAction) {
    // Get permissions
    case 'permissions':
        $faqId = Filter::filterInput(INPUT_GET, 'faq-id', FILTER_VALIDATE_INT);

        $faqPermission = new FaqPermission($faqConfig);

        $response->setStatusCode(Response::HTTP_OK);
        $response->setData(
            [
                'user' => $faqPermission->get(FaqPermission::USER, $faqId),
                'group' => $faqPermission->get(FaqPermission::GROUP, $faqId)
            ]
        );
        $response->send();
        break;

    // save active FAQs
    case 'save_active_records':
        $postData = json_decode(file_get_contents('php://input', true));

        $faqIds = Filter::filterArray($postData->faqIds);
        $faqLanguage = Filter::filterVar($postData->faqLanguage, FILTER_SANITIZE_SPECIAL_CHARS);
        $checked = Filter::filterVar($postData->checked, FILTER_VALIDATE_BOOLEAN);

        if (
            $user->perm->hasPermission($user->getUserId(), 'approverec') &&
            Token::getInstance()->verifyToken('faq-overview', $postData->csrf)
        ) {
            if (!empty($faqIds)) {
                $faq = new Faq($faqConfig);

                foreach ($faqIds as $faqId) {
                    if (Language::isASupportedLanguage($faqLanguage)) {
                        $success = $faq->updateRecordFlag($faqId, $faqLanguage, $checked ?? false, 'active');
                    }
                }
                $response->setStatusCode(Response::HTTP_OK);
                $response->setData(['success' => $success]);
            }
        } else {
            $response->setStatusCode(Response::HTTP_UNAUTHORIZED);
            $response->setData(['error' => Translation::get('err_NotAuth')]);
        }
        $response->send();
        break;

    // save sticky FAQs
    case 'save_sticky_records':
        $postData = json_decode(file_get_contents('php://input', true));

        $faqIds = Filter::filterArray($postData->faqIds);
        $faqLanguage = Filter::filterVar($postData->faqLanguage, FILTER_SANITIZE_SPECIAL_CHARS);
        $checked = Filter::filterVar($postData->checked, FILTER_VALIDATE_BOOLEAN);

        if (
            $user->perm->hasPermission($user->getUserId(), 'edit_faq') &&
            Token::getInstance()->verifyToken('faq-overview', $postData->csrf)
        ) {
            if (!empty($faqIds)) {
                $faq = new Faq($faqConfig);
                foreach ($faqIds as $faqId) {
                    if (Language::isASupportedLanguage($faqLanguage)) {
                        $success = $faq->updateRecordFlag($faqId, $faqLanguage, $checked ?? false, 'sticky');
                    }
                }
                $response->setStatusCode(Response::HTTP_OK);
                $response->setData(['success' => $success]);
            }
        } else {
            $response->setStatusCode(Response::HTTP_UNAUTHORIZED);
            $response->setData(['error' => Translation::get('err_NotAuth')]);
        }
        $response->send();
        break;

    // search FAQs for suggestions
    case 'search_records':
        $postData = json_decode(file_get_contents('php://input', true));

        if (
            $user->perm->hasPermission($user->getUserId(), 'edit_faq') &&
            Token::getInstance()->verifyToken('edit-faq', $postData->csrf)
        ) {

            $faqPermission = new FaqPermission($faqConfig);
            $faqSearch = new Search($faqConfig);
            $faqSearch->setCategory(new Category($faqConfig));
            $faqSearchResult = new SearchResultSet($user, $faqPermission, $faqConfig);
            $searchResult = '';
            $searchString = Filter::filterVar($postData->search, FILTER_SANITIZE_SPECIAL_CHARS);

            if (!is_null($searchString)) {
                $searchResult = $faqSearch->search($searchString, false);

                $faqSearchResult->reviewResultSet($searchResult);

                $searchHelper = new SearchHelper($faqConfig);
                $searchHelper->setSearchTerm($searchString);

                $response->setStatusCode(Response::HTTP_OK);
                $response->setData(
                    ['success' => $searchHelper->renderAdminSuggestionResult($faqSearchResult) ]
                );
            }
        } else {
            $response->setStatusCode(Response::HTTP_UNAUTHORIZED);
            $response->setData(['error' => Translation::get('err_NotAuth')]);
        }
        $response->send();
        break;

    // delete FAQs
    case 'delete_record':
        $deleteData = json_decode(file_get_contents('php://input', true));

        if (
            $user->perm->hasPermission($user->getUserId(), 'delete_faq') &&
            Token::getInstance()->verifyToken('faq-overview', $deleteData->csrf)
        ) {
            $recordId = Filter::filterVar($deleteData->record_id, FILTER_VALIDATE_INT);
            $recordLang = Filter::filterVar($deleteData->record_lang, FILTER_SANITIZE_SPECIAL_CHARS);

            $logging = new AdminLog($faqConfig);
            $logging->log($user, 'Deleted FAQ ID ' . $recordId);

            try {
                $faq->deleteRecord($recordId, $recordLang);
            } catch (FileException | AttachmentException $e) {
                $response->setStatusCode(Response::HTTP_BAD_REQUEST);
                $response->setData(['error' => $e->getMessage()]);
                $response->send();
            }
            $response->setStatusCode(Response::HTTP_OK);
            $response->setData(['success' => Translation::get('ad_entry_delsuc') ]);
        } else {
            $response->setStatusCode(Response::HTTP_UNAUTHORIZED);
            $response->setData(['error' => Translation::get('err_NotAuth')]);
        }
        $response->send();
        break;

    // delete open questions
    case 'delete_question':
        $deleteData = json_decode(file_get_contents('php://input', true));

        if (!Token::getInstance()->verifyToken('delete-questions', $deleteData->data->{'pmf-csrf-token'})) {
            $response->setStatusCode(Response::HTTP_UNAUTHORIZED);
            $response->setData(['error' => Translation::get('err_NotAuth')]);
            exit(1);
        }

        if ($user->perm->hasPermission($user->getUserId(), 'delquestion')) {
            $questionIds = $deleteData->data->{'questions[]'};
            $question = new Question($faqConfig);

            if (!is_null($questionIds)) {
                if (!is_array($questionIds)) {
                    $questionIds = [$questionIds];
                }
                foreach ($questionIds as $questionId) {
                    $question->deleteQuestion((int)$questionId);
                }

                $response->setStatusCode(Response::HTTP_OK);
                $response->setData(['success' => Translation::get('ad_open_question_deleted')]);
            } else {
                $response->setStatusCode(Response::HTTP_UNAUTHORIZED);
                $response->setData(['error' => Translation::get('err_NotAuth')]);
            }
            $response->send();
        }
        break;
}

// -x-

<?php

/**
 * Private phpMyFAQ Admin API: handling of Ajax group calls.
 *
 * This Source Code Form is subject to the terms of the Mozilla Public License,
 * v. 2.0. If a copy of the MPL was not distributed with this file, You can
 * obtain one at https://mozilla.org/MPL/2.0/.
 *
 * @package   phpMyFAQ
 * @author    Thorsten Rinne <thorsten@phpmyfaq.de>
 * @copyright 2009-2023 phpMyFAQ Team
 * @license   https://www.mozilla.org/MPL/2.0/ Mozilla Public License Version 2.0
 * @link      https://www.phpmyfaq.de
 * @since     2009-04-06
 */

use phpMyFAQ\Filter;
use phpMyFAQ\Permission\MediumPermission;
use Symfony\Component\HttpFoundation\JsonResponse;
use Symfony\Component\HttpFoundation\Request;
use Symfony\Component\HttpFoundation\Response;

if (!defined('IS_VALID_PHPMYFAQ')) {
    http_response_code(400);
    exit();
}

//
// Create Request & Response
//
$response = new JsonResponse();
$request = Request::createFromGlobals();

$ajaxAction = Filter::filterVar($request->query->get('ajaxaction'), FILTER_SANITIZE_SPECIAL_CHARS);
$groupId = Filter::filterVar($request->query->get('group_id'), FILTER_VALIDATE_INT);

if (
    $user->perm->hasPermission($user->getUserId(), 'add_user') ||
    $user->perm->hasPermission($user->getUserId(), 'edit_user') ||
    $user->perm->hasPermission($user->getUserId(), 'delete_user') ||
    $user->perm->hasPermission($user->getUserId(), 'editgroup')
) {
    // pass the user id of the current user, so it'll check which group he belongs to
    $groupList = ($user->perm instanceof MediumPermission) ? $user->perm->getAllGroups($user) : [];
    $userList = $user->getAllUsers(true, false);

    // Returns all groups
    if ('get_all_groups' == $ajaxAction) {
        $groups = [];
        foreach ($groupList as $groupId) {
            $data = $user->perm->getGroupData($groupId);
            $groups[] = [
                'group_id' => $data['group_id'],
                'name' => $data['name'],
            ];
        }
        $response->setStatusCode(Response::HTTP_OK);
        $response->setData($groups);
    }

    // Return the group data
    if ('get_group_data' == $ajaxAction) {
        $response->setStatusCode(Response::HTTP_OK);
        $response->setData($user->perm->getGroupData($groupId));
    }

    // Return the group rights
    if ('get_group_rights' == $ajaxAction) {
        $response->setStatusCode(Response::HTTP_OK);
        $response->setData($user->perm->getGroupRights($groupId));
    }

    // Return all users
    if ('get_all_users' == $ajaxAction) {
        $users = [];
        foreach ($userList as $singleUser) {
            $user->getUserById($singleUser, true);
            $users[] = [
                'user_id' => $user->getUserId(),
                'login' => $user->getLogin(),
            ];
        }
        $response->setStatusCode(Response::HTTP_OK);
        $response->setData($users);
    }

    // Returns all group members
    if ('get_all_members' == $ajaxAction) {
        $memberList = $user->perm->getGroupMembers($groupId);
        $members = [];
        foreach ($memberList as $singleMember) {
            $user->getUserById($singleMember, true);
            $members[] = [
                'user_id' => $user->getUserId(),
                'login' => $user->getLogin(),
            ];
        }
        $response->setStatusCode(Response::HTTP_OK);
        $response->setData($members);
    }

    $response->send();
}

// -x-
/*
Copyright The Helm Authors.
Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
*/

package chartutil

import (
	"fmt"
	"strconv"

	"github.com/Masterminds/semver/v3"
	"k8s.io/client-go/kubernetes/scheme"

	apiextensionsv1 "k8s.io/apiextensions-apiserver/pkg/apis/apiextensions/v1"
	apiextensionsv1beta1 "k8s.io/apiextensions-apiserver/pkg/apis/apiextensions/v1beta1"

	helmversion "helm.sh/helm/v3/internal/version"
)

var (
	// The Kubernetes version can be set by LDFLAGS. In order to do that the value
	// must be a string.
	k8sVersionMajor = "1"
	k8sVersionMinor = "20"

	// DefaultVersionSet is the default version set, which includes only Core V1 ("v1").
	DefaultVersionSet = allKnownVersions()

	// DefaultCapabilities is the default set of capabilities.
	DefaultCapabilities = &Capabilities{
		KubeVersion: KubeVersion{
			Version: fmt.Sprintf("v%s.%s.0", k8sVersionMajor, k8sVersionMinor),
			Major:   k8sVersionMajor,
			Minor:   k8sVersionMinor,
		},
		APIVersions: DefaultVersionSet,
		HelmVersion: helmversion.Get(),
	}
)

// Capabilities describes the capabilities of the Kubernetes cluster.
type Capabilities struct {
	// KubeVersion is the Kubernetes version.
	KubeVersion KubeVersion
	// APIversions are supported Kubernetes API versions.
	APIVersions VersionSet
	// HelmVersion is the build information for this helm version
	HelmVersion helmversion.BuildInfo
}

func (capabilities *Capabilities) Copy() *Capabilities {
	return &Capabilities{
		KubeVersion: capabilities.KubeVersion,
		APIVersions: capabilities.APIVersions,
		HelmVersion: capabilities.HelmVersion,
	}
}

// KubeVersion is the Kubernetes version.
type KubeVersion struct {
	Version string // Kubernetes version
	Major   string // Kubernetes major version
	Minor   string // Kubernetes minor version
}

// String implements fmt.Stringer
func (kv *KubeVersion) String() string { return kv.Version }

// GitVersion returns the Kubernetes version string.
//
// Deprecated: use KubeVersion.Version.
func (kv *KubeVersion) GitVersion() string { return kv.Version }

// ParseKubeVersion parses kubernetes version from string
func ParseKubeVersion(version string) (*KubeVersion, error) {
	sv, err := semver.NewVersion(version)
	if err != nil {
		return nil, err
	}
	return &KubeVersion{
		Version: "v" + sv.String(),
		Major:   strconv.FormatUint(sv.Major(), 10),
		Minor:   strconv.FormatUint(sv.Minor(), 10),
	}, nil
}

// VersionSet is a set of Kubernetes API versions.
type VersionSet []string

// Has returns true if the version string is in the set.
//
//	vs.Has("apps/v1")
func (v VersionSet) Has(apiVersion string) bool {
	for _, x := range v {
		if x == apiVersion {
			return true
		}
	}
	return false
}

func allKnownVersions() VersionSet {
	// We should register the built in extension APIs as well so CRDs are
	// supported in the default version set. This has caused problems with `helm
	// template` in the past, so let's be safe
	apiextensionsv1beta1.AddToScheme(scheme.Scheme)
	apiextensionsv1.AddToScheme(scheme.Scheme)

	groups := scheme.Scheme.PrioritizedVersionsAllGroups()
	vs := make(VersionSet, 0, len(groups))
	for _, gv := range groups {
		vs = append(vs, gv.String())
	}
	return vs
}
// -x-
/*
Copyright The Helm Authors.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
*/

package chartutil

import (
	"os"
	"path/filepath"

	"github.com/pkg/errors"
	"sigs.k8s.io/yaml"

	"helm.sh/helm/v3/pkg/chart"
)

// LoadChartfile loads a Chart.yaml file into a *chart.Metadata.
func LoadChartfile(filename string) (*chart.Metadata, error) {
	b, err := os.ReadFile(filename)
	if err != nil {
		return nil, err
	}
	y := new(chart.Metadata)
	err = yaml.Unmarshal(b, y)
	return y, err
}

// SaveChartfile saves the given metadata as a Chart.yaml file at the given path.
//
// 'filename' should be the complete path and filename ('foo/Chart.yaml')
func SaveChartfile(filename string, cf *chart.Metadata) error {
	// Pull out the dependencies of a v1 Chart, since there's no way
	// to tell the serializer to skip a field for just this use case
	savedDependencies := cf.Dependencies
	if cf.APIVersion == chart.APIVersionV1 {
		cf.Dependencies = nil
	}
	out, err := yaml.Marshal(cf)
	if cf.APIVersion == chart.APIVersionV1 {
		cf.Dependencies = savedDependencies
	}
	if err != nil {
		return err
	}
	return os.WriteFile(filename, out, 0644)
}

// IsChartDir validate a chart directory.
//
// Checks for a valid Chart.yaml.
func IsChartDir(dirName string) (bool, error) {
	if fi, err := os.Stat(dirName); err != nil {
		return false, err
	} else if !fi.IsDir() {
		return false, errors.Errorf("%q is not a directory", dirName)
	}

	chartYaml := filepath.Join(dirName, ChartfileName)
	if _, err := os.Stat(chartYaml); os.IsNotExist(err) {
		return false, errors.Errorf("no %s exists in directory %q", ChartfileName, dirName)
	}

	chartYamlContent, err := os.ReadFile(chartYaml)
	if err != nil {
		return false, errors.Errorf("cannot read %s in directory %q", ChartfileName, dirName)
	}

	chartContent := new(chart.Metadata)
	if err := yaml.Unmarshal(chartYamlContent, &chartContent); err != nil {
		return false, err
	}
	if chartContent == nil {
		return false, errors.Errorf("chart metadata (%s) missing", ChartfileName)
	}
	if chartContent.Name == "" {
		return false, errors.Errorf("invalid chart (%s): name must not be empty", ChartfileName)
	}

	return true, nil
}
// -x-