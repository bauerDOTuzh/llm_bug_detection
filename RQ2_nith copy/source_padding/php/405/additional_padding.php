<?php
// -x-
public function init()
{
    add_filter('wp_sms_registered_integration_tabs', function ($tabs) {
        $tabs['forminator'] = __('Forminator', 'wp-sms');
        return $tabs;
    });

    add_filter('wp_sms_forminator_settings', array($this, 'setting_fields'));

    $forminator = new Forminator();
    $forminator->init();
}
// -x-
public function setting_fields($options)
{
    $forminator_forms = array();

    if (class_exists('Forminator')) {
        $forms = Forminator_API::get_forms(null, 1, 20, "publish");

        if (empty($forms)) {
            $forminator_forms['forminator_notify_form'] = array(
                'id'   => 'forminator_notify_form',
                'name' => esc_html__('No data', 'wp-sms'),
                'type' => 'notice',
                'desc' => esc_html__('There is no form available on Forminator plugin, please first add your forms.', 'wp-sms')
            );
        }

        foreach ($forms as $form) {
            $formFields                                                       = Forminator::formFields($form->id);
            $forminator_forms['forminator_notify_form_' . $form->id]          = array(
                'id'   => 'forminator_notify_form_' . $form->id,
                // translators: %s: Form name
                'name' => sprintf(__('Form notifications (%s)', 'wp-sms'), $form->name),
                'type' => 'header',
                // translators: %s: Form name
                'desc' => sprintf(__('By enabling this option you can send SMS notification once the %s form is submitted', 'wp-sms'), $form->name),
                'doc'  => '',
            );
            $forminator_forms['forminator_notify_enable_form_' . $form->id]   = array(
                'id'      => 'forminator_notify_enable_form_' . $form->id,
                'name'    => __('Send SMS to a number', 'wp-sms'),
                'type'    => 'checkbox',
                'options' => $options,
            );
            $forminator_forms['forminator_notify_receiver_form_' . $form->id] = array(
                'id'   => 'forminator_notify_receiver_form_' . $form->id,
                'name' => __('Phone number(s)', 'wp-sms'),
                'type' => 'text',
                'desc' => __('Enter the mobile number(s) to receive SMS, to separate numbers, use the latin comma.', 'wp-sms')
            );
            $forminator_forms['forminator_notify_message_form_' . $form->id]  = array(
                'id'   => 'forminator_notify_message_form_' . $form->id,
                'name' => __('Message body', 'wp-sms'),
                'type' => 'textarea',
                'desc' => __('Enter your message content.', 'wp-sms') . '<br>' .
                    $this->printVariables(
                        NotificationFactory::getForminator($form->id)->getVariables()
                    )
            );

            if ($formFields) {
                $forminator_forms['forminator_notify_enable_field_form_' . $form->id]   = array(
                    'id'      => 'forminator_notify_enable_field_form_' . $form->id,
                    'name'    => __('Send SMS to field', 'wp-sms'),
                    'type'    => 'checkbox',
                    'options' => $options,
                );
                $forminator_forms['forminator_notify_receiver_field_form_' . $form->id] = array(
                    'id'      => 'forminator_notify_receiver_field_form_' . $form->id,
                    'name'    => __('A field of the form', 'wp-sms'),
                    'type'    => 'select',
                    'options' => $formFields,
                    'desc'    => __('Select the field of your form.', 'wp-sms')
                );
                $forminator_forms['forminator_notify_message_field_form_' . $form->id]  = array(
                    'id'   => 'forminator_notify_message_field_form_' . $form->id,
                    'name' => __('Message body', 'wp-sms'),
                    'type' => 'textarea',
                    'desc' => __('Enter your message content.', 'wp-sms') . '<br>' .
                        $this->printVariables(
                            NotificationFactory::getForminator($form->id)->getVariables()
                        )
                );
            }
        }
    } else {
        $forminator_forms['forminator_notify_form'] = array(
            'id'   => 'forminator_notify_form',
            'name' => __('Not active', 'wp-sms'),
            'type' => 'notice',
            'desc' => __('Forminator plugin should be enable to run this tab', 'wp-sms')
        );
    }
    return $forminator_forms;
}
// -x-
private function printVariables($variables)
{
    $result = "";
    foreach ($variables as $key => $value) {
        preg_match("/(%field-|%)(.+)*\%/", $key, $match);
        $label  = $match[1] ? $match[2] : "";
        $result .= esc_html($label) . ": <code>" . esc_html($key) . "</code> ";
    }
    return $result;
}
// -x-
private function getData($key, $default = false)
{
    $value = Option::getOption($key);

    return !empty($value) ? $value : $default;
}
// -x-
public function isEnabled()
{
    return $this->getData('chatbox_message_button');
}
// -x-
public function getTitle()
{
    return $this->getData('chatbox_title', __('Chat with Us!', 'wp-sms'));
}

public function getButtonText()
{
    return $this->getData('chatbox_button_text', __('Talk to Us', 'wp-sms'));
}

public function getFooterText()
{
    return $this->getData('chatbox_footer_text', __('Chat with us on WhatsApp for instant support!', 'wp-sms'));
}

public function getFooterLinkUrl()
{
    return $this->getData('chatbox_footer_link_url');
}

public function getFooterLinkTitle()
{
    return $this->getData('chatbox_footer_link_title', __('Related Articles', 'wp-sms'));
}

public function getFooterTextColor()
{
    return $this->getData('chatbox_footer_text_color');
}

public function getTextColor($default = false)
{
    return $this->getData('chatbox_text_color', $default);
}

public function getColor()
{
    return $this->getData('chatbox_color');
}

public function getAnimationEffect()
{
    return $this->getData('chatbox_animation_effect');
}
// -x-
public function isLinkEnabled()
{
    return $this->getData('chatbox_links_enabled');
}
// -x-
public function isFooterLogoEnabled()
{
    return $this->getData('chatbox_disable_logo', 'enable') == 'enable';
}
// -x-
public function getLinkTitle()
{
    return $this->getData('chatbox_links_title', __('Quick Links', 'wp-sms'));
}
// -x-
public function getButtonPosition()
{
    return $this->getData('chatbox_button_position', 'bottom_right');
}

public function fetchTeamMembers()
{
    $teams         = $this->getData('chatbox_team_members', []);
    $processedTeam = [];

    // Loop through each team member
    foreach ($teams as &$teamMember) {
        // Check and replace empty values with sample data
        if ($teamMember['member_name'] == '') {
            $teamMember['member_name'] = __('Emily Brown', 'wp-sms');
        }
        if ($teamMember['member_role'] == '') {
            $teamMember['member_role'] = __('Marketing Manager', 'wp-sms');
        }
        if ($teamMember['member_availability'] == '') {
            $teamMember['member_availability'] = __('Available 10AM-5PM PST', 'wp-sms');
        }
        if ($teamMember['member_photo'] == '') {
            $teamMember['member_photo'] = WP_SMS_URL . 'assets/images/avatar.png';
        }
        if ($teamMember['member_contact_value'] == '') {
            $teamMember['member_contact_value'] = '+1122334455';
        }
        if ($teamMember['member_contact_type'] == '') {
            $teamMember['member_contact_type'] = 'whatsapp';
        }

        // Process each team member
        $teamMember['contact_link']      = $this->generateContactLink($teamMember['member_contact_type'], $teamMember['member_contact_value']);
        $teamMember['contact_link_icon'] = sprintf('%s/assets/images/chatbox/icon-%s.svg', WP_SMS_URL, $teamMember['member_contact_type']);

        $processedTeam[] = $teamMember;
    }

    return $processedTeam;
}
// -x-
private function generateContactLink($type, $value)
{
    $value = trim($value);

    if ($type === 'whatsapp') {
        $linkUrl = 'https://wa.me/' . $value;
    } else if ($type === 'telegram') {
        $linkUrl = 'https://t.me/' . $value;
    } else if ($type === 'facebook') {
        $linkUrl = 'https://me.me/' . $value;
    } else if ($type === 'sms') {
        $linkUrl = 'sms:' . $value;
    } else if ($type === 'email') {
        $linkUrl = 'mailto:' . $value;
    } else {
        $linkUrl = 'tel:' . $value;
    }

    return apply_filters('wp_sms_chatbox_contact_link', $linkUrl, $type, $value);
}
// -x-
public function fetchLinks()
{
    $links         = $this->getData('chatbox_links', []);
    $processedLink = [];

    // Loop through each team member
    foreach ($links as &$teamMember) {
        // Check and replace empty values with sample data
        if ($teamMember['chatbox_link_title'] == '') {
            $teamMember['chatbox_link_title'] = __('Troubleshooting Common Issues', 'wp-sms');
        }
        if ($teamMember['chatbox_link_url'] == '') {
            $teamMember['chatbox_link_url'] = site_url('troubleshooting');
        }

        $processedLink[] = $teamMember;
    }

    return $processedLink;
}
// -x-
private $mobileFieldHandler = [
    'disable'                        => \WP_SMS\User\MobileFieldHandler\DefaultFieldHandler::class,
    'add_mobile_field_in_profile'    => \WP_SMS\User\MobileFieldHandler\WordPressMobileFieldHandler::class,
    'add_mobile_field_in_wc_billing' => \WP_SMS\User\MobileFieldHandler\WooCommerceAddMobileFieldHandler::class,
    'use_phone_field_in_wc_billing'  => \WP_SMS\User\MobileFieldHandler\WooCommerceUsePhoneFieldHandler::class,
];
// -x-
public function getHandler()
{
    $field = wp_sms_get_option('add_mobile_field');

    $this->mobileFieldHandler = apply_filters('wp_sms_mobile_filed_handler', $this->mobileFieldHandler);

    if (isset($this->mobileFieldHandler[$field]) && class_exists($this->mobileFieldHandler[$field])) {
        return new $this->mobileFieldHandler[$field];
    }

    /**
     * WooCommerce Backward compatibility
     * This will use the exists billing phone field in checkout even the option is not configured.
     */
    if (class_exists('WooCommerce')) {
        Option::updateOption('add_mobile_field', 'use_phone_field_in_wc_billing');

        return new $this->mobileFieldHandler['use_phone_field_in_wc_billing'];
    }

    /**
     * Old version Backward compatibility
     */
    Option::updateOption('add_mobile_field', 'disable');

    return new $this->mobileFieldHandler['disable'];
}
// -x-
public function init()
{
    $handler = $this->getHandler();

    if ($handler) {
        $handler->register();
    }
}
// -x-

private $mobileNumber;
private $userId;

public function __construct($mobileNumber)
{
    // Sanitize and prepare mobile number
    $this->mobileNumber = str_replace('+', '', Helper::sanitizeMobileNumber($mobileNumber));
}
// -x-
/**
 * Register user with phone number
 */
public function register()
{
    $result = $this->registerUser();

    // Store user meta data
    if (!is_wp_error($result)) {
        $this->saveMetas();
    }

    return $result;
}
// -x-
private function registerUser()
{
    $this->userId = register_new_user(
        $this->generateUniqueUsername(),
        $this->generateUniqueEmail()
    );

    return $this->userId;
}
// -x-
private function saveMetas()
{
    update_user_meta($this->userId, Helper::getUserMobileFieldName(), $this->mobileNumber);
}
// -x-
/**
 * Generate a unique username
 *
 * @return string
 */
public function generateUniqueUsername()
{
    $username = 'phone_' . $this->mobileNumber;

    /**
     * Allow to modify the username with filter
     */
    return apply_filters('wp_sms_registration_username', $username, $this->mobileNumber);
}

/**
 * Generate a unique email address
 */
public function generateUniqueEmail()
{
    $siteUrl    = get_bloginfo('url');
    $siteDomain = parse_url($siteUrl)['host'];

    if (strpos($siteDomain, '.') == false) {
        $siteDomain = $siteDomain . '.' . $siteDomain;
    }

    $emailAddress = $this->mobileNumber . '@' . $siteDomain;

    /**
     * Allow to modify the email address with filter
     */
    return apply_filters('wp_sms_registration_email', $emailAddress, $this->mobileNumber);
}
// -x-

protected $id = 'wp-sms-stats-widget';
protected $name = 'WP SMS Stats';

/**
 * Preparations before rendering
 *
 * @return void
 */

/**
 * Render the widget
 *
 * @return void
 */
public function render()
{
    echo Helper::loadTemplate('admin/dashboard-widget.php'); // phpcs:ignore WordPress.Security.EscapeOutput.OutputNotEscaped
}
// -x-
/**
 * Get widget's dashboard script localization data
 *
 * @return void
 */
public function getLocalizationData()
{
    $widgetData['localization'] = [
        'successful' => esc_html__('Successful', 'wp-sms'),
        'failed'     => esc_html__('Failed', 'wp-sms'),
        'plain'      => esc_html__('Plain', 'wp-sms'),
    ];

    /**
     * @param \DatePeriod $period
     * @param string $format
     */
    $getResults = function (DatePeriod $period, string $format) {
        global $wpdb;

        $dates = iterator_to_array($period);
        sort($dates);

        $datasets = [];

        for ($i = 0; $i < sizeof($dates) - 1; $i++) {
            $firstDate  = $dates[$i];
            $secondDate = $dates[$i + 1];

            $label = $firstDate->format($format);

            $results = $wpdb->get_results(
                $wpdb->prepare("select `status`, count(*) as count from `{$wpdb->prefix}sms_send` where `date` between DATE(%s) and DATE(%s) group by `status`", $firstDate->format('Y-m-d'), $secondDate->format('Y-m-d'))
            );

            foreach ($results as $key => $result) {
                $results[$result->status] = $result->count;
                unset($results[$key]);
            }

            $datasets['successful'][$label] = $results['success'] ?? 0;
            $datasets['failure'][$label]    = $results['error'] ?? 0;
        }

        return $datasets;
    };

    $sentMessages['last_7_days']   = $getResults(
        new DatePeriod(new DateTime('tomorrow'), DateInterval::createFromDateString('-1 day'), 7),
        'd D'
    );
    $sentMessages['last_30_days']  = $getResults(
        new DatePeriod(new DateTime('tomorrow'), DateInterval::createFromDateString('-1 day'), 30),
        'd M'
    );
    $sentMessages['this_year']     = $getResults(
        new DatePeriod(new DateTime('first day of jan'), DateInterval::createFromDateString('+1 month'), (new DateTime('first day of next month'))->modify('+1 second')),
        'M'
    );
    $sentMessages['last_12_month'] = $getResults(
        new DatePeriod(new DateTime('first day of -11 month'), DateInterval::createFromDateString('+1 month'), (new DateTime('first day of next month'))->modify('+1 second')),
        'M'
    );

    $widgetData['send-messages-stats'] = $sentMessages;

    return $widgetData;
}
// -x-
/**
 * @var array
 */
private $widgets = [
    'StatsWidget' => Widgets\StatsWidget::class,
];

/**
 * Init widgets
 *
 * @return void
 */
public static function init()
{
    $instance = new self;
    $instance->includeRequirements();
    $instance->loadWidgets();
    $instance->registerAssets();
}
// -x-
/**
 * Include requirements
 *
 * @return void
 */
private function includeRequirements()
{
    require_once WP_SMS_DIR . 'src/Widget/AbstractWidget.php';
}

/**
 * Require files in widgets folder
 *
 * @return void
 */
private function loadWidgets()
{
    foreach ($this->widgets as $fileName => $widget) {
        $file = WP_SMS_DIR . "src/Widget/Widgets/{$fileName}.php";

        if (file_exists($file)) {
            require_once $file;
        }

        if (is_subclass_of($widget, AbstractWidget::class)) {
            (new $widget)->register();
        }
    }
}
// -x-
/**
 * Register widgets common assets
 *
 * @return void
 */
private function registerAssets()
{
}

    /**
 * Enqueue a script.
 *
 * @param string $handle The script handle.
 * @param string $src The source URL of the script.
 * @param array $deps An array of script dependencies.
 * @param array $localize An array of data to be localized.
 * @param bool $inFooter Whether to enqueue the script in the footer.
 * @return void
 * @example Assets::script('admin', 'dist/admin.js', ['jquery'], ['foo' => 'bar'], true);
 */
public static function script($handle, $src, $deps = [], $localize = [], $inFooter = false)
{
    $object = self::getObject($handle);
    $handle = self::getHandle($handle);

    wp_enqueue_script($handle, self::getSrc($src), $deps, WP_SMS_VERSION, $inFooter);

    if ($localize) {
        $localize = apply_filters("wp_sms_localize_{$handle}", $localize);

        wp_localize_script($handle, $object, $localize);
    }
}
// -x-
/**
 * Register a script.
 *
 * @param string $handle The script handle.
 * @param string $src The source URL of the script.
 * @param array $deps An array of script dependencies.
 * @param string|null $version Optional. The version of the script. Defaults to plugin version.
 * @param bool $inFooter Whether to enqueue the script in the footer.
 * @return void
 * @example Assets::registerScript('chartjs', 'js/chart.min.js', [], '3.7.1');
 */
public static function registerScript($handle, $src, $deps = [], $version = null, $inFooter = false)
{
    // Get the handle for the script
    $handle = self::getHandle($handle);

    // Get the version of the script, if not provided, use the default version
    if ($version === null) {
        $version = WP_SMS_VERSION;
    }

    // Register the script with WordPress
    wp_register_script($handle, self::getSrc($src), $deps, $version, $inFooter);
}
// -x-
/**
 * Enqueue a style.
 *
 * @param string $handle The style handle.
 * @param string $src The source URL of the style.
 * @param array $deps An array of style dependencies.
 * @param string $media The context which style needs to be loaded: all, print, or screen
 * @return void
 * @example Assets::style('admin', 'dist/admin.css', ['jquery'], 'all');
 */
public static function style($handle, $src, $deps = [], $media = 'all')
{
    wp_enqueue_style(self::getHandle($handle), self::getSrc($src), $deps, WP_SMS_VERSION, $media);
}

/**
 * Get the handle for the script/style.
 *
 * @param string $handle The script/style handle.
 * @return string
 */
private static function getHandle($handle)
{
    return sprintf('wp-sms-%s', strtolower($handle));
}
// -x-
/**
 * Get the source URL for the script/style.
 *
 * @param string $src The source URL.
 * @return string
 */
private static function getSrc($src)
{
    return Helper::getPluginAssetUrl($src);
}

/**
 * Get the object name for script localization.
 *
 * @param string $handle The script handle.
 * @return string
 */
private static function getObject($handle)
{
    $parts          = explode('-', $handle);
    $camelCaseParts = array_map('ucfirst', $parts);

    return 'WP_Sms_' . implode('_', $camelCaseParts) . '_Object';
}
// -x-
protected $webhookType;
protected $webhookAction;

/**
 * @return void|WP_Error
 */
public static function boot()
{
    try {

        $class  = self::getClassName();
        $action = new $class;

        $action->init();

    } catch (Exception $e) {
        error_log($e->getMessage());
    }
}
// -x-
public function init()
{
    add_action($this->webhookAction['actionName'], [$this, 'run'], 10, $this->webhookAction['acceptArgs']);
}

public static function getClassName()
{
    return get_called_class();
}

protected function fetchWebhooks()
{
    return WebhookFactory::getWebhooks($this->webhookType);
}
// -x-
/**
 * @param $url
 * @param $data
 * @return void|WP_Error
 * @throws Exception
 */
protected function execute($url, $data)
{
    try {

        $params = array(
            'method'  => 'POST',
            'body'    => wp_json_encode($data),
            'headers' => array(
                'Content-Type'           => 'application/json',
                'X-WP-SMS-Webhook-Event' => $this->webhookType,
                'X-WP-SMS-Version'       => WP_SMS_VERSION,
            )
        );

        $response = wp_safe_remote_request(trim($url), $params);

        if (is_wp_error($response)) {
            throw new Exception($response->get_error_message());
        }

        $responseCode = wp_remote_retrieve_response_code($response);
        $responseBody = wp_remote_retrieve_body($response);

        if (in_array($responseCode, [200, 201, 202]) === false) {
            // translators: %s: Error message
            throw new Exception(sprintf(esc_html__('Failed to get success response, %s', 'wp-sms'), print_r($responseBody, 1)));
        }

    } catch (\Throwable $e) {
        error_log(sprintf('WP SMS: The provided webhook could not be executed, Error Message: %s', $e->getMessage()));
    }
}