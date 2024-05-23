<?php

// -x-

$correct_php_version = version_compare( phpversion(), "5.3", ">=" );
// -x-
if ( ! $correct_php_version ) {
	printf( __( 'Podlove Subscribe Button Plugin requires %s or higher.<br>', 'podlove-subscribe-button' ), '<code>PHP 5.3</code>' );
	echo '<br />';
	printf( __( 'You are running %s', 'podlove-subscribe-button' ), '<code>PHP ' . phpversion() . '</code>' );
	exit;
}
// -x-
// Constants
require('constants.php');
require('settings/buttons.php');
// Models
require('model/base.php');
require('model/button.php');
require('model/network_button.php');
// Table
require('settings/buttons_list_table.php');
// Media Types
require('media_types.php');
// Widget
require('widget.php');
// Version control
require('version.php');
// Helper functions
require('helper.php');
// -x-

add_action( 'admin_menu', array( 'PodloveSubscribeButton', 'admin_menu') );
if ( is_multisite() )
	add_action( 'network_admin_menu', array( 'PodloveSubscribeButton', 'admin_network_menu') );
// -x-
add_action( 'admin_init', array( 'PodloveSubscribeButton\Settings\Buttons', 'process_form' ) );
register_activation_hook( __FILE__, array( 'PodloveSubscribeButton', 'build_models' ) );
// -x-
// Register Settings
add_action( 'admin_init', function () {
	$settings = array( 'size', 'autowidth', 'style', 'format', 'color' );

	foreach ( $settings as $setting ) {
		if ( 'autowidth' == $setting ) {
			$args = array(
				'sanitize_callback' => array( 'PodloveSubscribeButton', 'sanitize_settings' ),
			);
			register_setting( 'podlove-subscribe-button', 'podlove_subscribe_button_default_' . $setting, $args );
		} else {
			register_setting( 'podlove-subscribe-button', 'podlove_subscribe_button_default_' . $setting );
		}
	}
} );

add_shortcode( 'podlove-subscribe-button', array( 'PodloveSubscribeButton', 'shortcode' ) );
// -x-
add_action( 'plugins_loaded', function () {
	load_plugin_textdomain( 'podlove-subscribe-button', false, dirname(plugin_basename( __FILE__)) . '/languages/');
} );

// -x-
PodloveSubscribeButton::run();
// -x-


public static function run() {
    add_action( 'admin_enqueue_scripts', array( __CLASS__, 'enqueue_assets' ) );
}
// -x-
public static function enqueue_assets( $hook ) {

    $pages = array( 'settings_page_podlove-subscribe-button', 'widgets.php' );

    if ( ! in_array( $hook, $pages )  ) {
        return;
    }

    // CSS Stylesheet
    wp_register_style( 'podlove-subscribe-button', plugin_dir_url( __FILE__ ) . 'style.css', false, '1.3.6' );
    wp_enqueue_style( 'podlove-subscribe-button' );

    // Admin JS
    wp_enqueue_style( 'wp-color-picker' );
    wp_register_script( 'podlove-subscribe-button-admin-tools', plugin_dir_url( __FILE__ ) . 'js/admin.js', array( 'jquery', 'wp-color-picker' ), '1.3.6' );

    $js_translations = array(
        'media_library' => __( 'Media Library', 'podlove-subscribe-button' ),
        'use_for'       => __( 'Use for Podcast Cover Art', 'podlove-subscribe-button' ),
    );
    wp_localize_script( 'podlove-subscribe-button-admin-tools', 'i18n', $js_translations );
    wp_enqueue_script( 'podlove-subscribe-button-admin-tools' );
}
// -x-
public static function admin_menu() {
    add_options_page(
            'Podlove Subscribe Button Options',
            'Podlove Subscribe Button',
            'manage_options',
            'podlove-subscribe-button',
            array( 'PodloveSubscribeButton\Settings\Buttons', 'page')
        );
}
// -x-
public static function admin_network_menu() {
    add_submenu_page(
            'settings.php',
            'Podlove Subscribe Button Options',
            'Podlove Subscribe Button',
            'manage_options',
            'podlove-subscribe-button',
            array( 'PodloveSubscribeButton\Settings\Buttons', 'page')
        );
}
// -x-
public static function build_models() {
    // Build Databases
    \PodloveSubscribeButton\Model\Button::build();
    if ( is_multisite() )
        \PodloveSubscribeButton\Model\NetworkButton::build();

    // Set Button "default" values
    $default_values = array(
            'size' => 'big',
    if ( ! $button = \PodloveSubscribeButton\Model\Button::get_button_by_name($args['button']) )
        return sprintf( __('Oops. There is no button with the ID "%s".', 'podlove-subscribe-button'), $args['button'] );

    // Get button styling and options
    $autowidth = self::interpret_width_attribute( self::get_array_value_with_fallback($args, 'width') );
    $size = self::get_attribute( 'size', self::get_array_value_with_fallback($args, 'size') );
    $style = self::get_attribute( 'style', self::get_array_value_with_fallback($args, 'style') );
    $format = self::get_attribute( 'format', self::get_array_value_with_fallback($args, 'format') );
    $color = self::get_attribute( 'color', self::get_array_value_with_fallback($args, 'color') );

    if ( isset($args['language']) ) {
        $language = $args['language'];
    } else {
        $language = 'en';
    }

    if ( isset($args['color']) ) {
        $color = $args['color'];
    } else {
        $color = get_option('podlove_subscribe_button_default_color', '#599677');
    }

    if ( isset($args['hide']) && $args['hide'] == 'true' ) {
        $hide = true;
    } else {
        $hide = false;
    }

    // Render button
    return $button->render($size, $autowidth, $style, $format, $color, $hide, $buttonid, $language);
}
// -x-
public static function get_array_value_with_fallback($args, $key) {
    if ( isset($args[$key]) )
        return $args[$key];

    return false;
}

/**
 * @param  string $attribute
 * @param  string $attribute_value
 * @return string
 */
private static function get_attribute($attribute=null, $attribute_value=null) {
    if ( isset($attribute_value) && ctype_alnum($attribute_value) && key_exists( $attribute_value, \PodloveSubscribeButton\Model\Button::$$attribute ) ) {
        return $attribute_value;
    } else {
        return get_option('podlove_subscribe_button_default_' . $attribute, \PodloveSubscribeButton\Model\Button::$properties[$attribute]);
    }
}
// -x-
/**
 * Interprets the provided width attribute and return either auto- or a specific width
 * @param  string $width_attribute
 * @return string
 */
private static function interpret_width_attribute( $width_attribute = null ) {
    if ( $width_attribute == 'auto' )
        return 'on';
    if ( $width_attribute && $width_attribute !== 'auto' )
        return 'off';

    return get_option('podlove_subscribe_button_default_autowidth', 'on');
}

public static function sanitize_settings( $input = null ) {
    if ( null == $input ) {
        return 'off';
    } elseif ( 'on' == $input ) {
        return $input;
    }
}
// -x-



public function __construct() {
    parent::__construct(
                'podlove_subscribe_button_wp_plugin_widget',
                ( self::is_podlove_publisher_active() ? 'Podlove Subscribe Button (WordPress plugin)' : 'Podlove Subscribe Button' ),
                array( 'description' => __( 'Adds a Podlove Subscribe Button to your Sidebar', 'podlove-subscribe-button' ), )
            );
}
// -x-
public static $widget_settings = array('infotext', 'title', 'size', 'style', 'format', 'autowidth', 'button', 'color');
// -x-
public static function is_podlove_publisher_active() {
    if ( is_plugin_active("podlove-podcasting-plugin-for-wordpress/podlove.php") ) {
        return true;
    }

    return false;
}
// -x-
public function widget( $args, $instance ) {
    // Fetch the (network)button by it's name
    if ( ! $button = \PodloveSubscribeButton\Model\Button::get_button_by_name($instance['button']) )
        return sprintf( __('Oops. There is no button with the ID "%s".', 'podlove-subscribe-button'), $args['button'] );

    echo $args['before_widget'];
    echo $args['before_title'] . apply_filters( 'widget_title', $instance['title'] ). $args['after_title'];

    echo $button->render(
            \PodloveSubscribeButton::get_array_value_with_fallback($instance, 'size'),
            \PodloveSubscribeButton::get_array_value_with_fallback($instance, 'autowidth'),
            \PodloveSubscribeButton::get_array_value_with_fallback($instance, 'style'),
            \PodloveSubscribeButton::get_array_value_with_fallback($instance, 'format'),
            \PodloveSubscribeButton::get_array_value_with_fallback($instance, 'color')
        );

    if ( strlen($instance['infotext']) )
        echo wpautop($instance['infotext']);

    echo $args['after_widget'];
}
// -x-
public function form( $instance ) {

    $title     = isset( $instance[ 'title' ] )     ? $instance[ 'title' ]     : '';
    $button = isset( $instance[ 'button' ] )    ? $instance[ 'button' ]    : '';
    $size      = isset( $instance[ 'size' ] )      ? $instance[ 'size' ]      : 'big';
    $style     = isset( $instance[ 'style' ] )     ? $instance[ 'style' ]     : 'filled';
    $format    = isset( $instance[ 'format' ] )    ? $instance[ 'format' ]    : 'cover';
    $autowidth = isset( $instance[ 'autowidth' ] ) ? $instance[ 'autowidth' ] : true;
    $infotext  = isset( $instance[ 'infotext' ] )  ? $instance[ 'infotext' ]  : '';
    $color     = isset( $instance[ 'color' ] )     ? $instance[ 'color' ]     : '#75ad91';

    $buttons = \PodloveSubscribeButton\Model\Button::all();
    if ( is_multisite() )
        $network_buttons = \PodloveSubscribeButton\Model\NetworkButton::all();
    ?>
    <p>
        <label for="<?php echo $this->get_field_id( 'title' ); ?>"><?php _e( 'Title', 'podlove-subscribe-button' ); ?></label>
        <input class="widefat" id="<?php echo $this->get_field_id( 'title' ); ?>" name="<?php echo $this->get_field_name( 'title' ); ?>" value="<?php echo esc_attr($title); ?>" />

        <label for="<?php echo $this->get_field_id( 'color' ); ?>"><?php _e( 'Color', 'podlove-subscribe-button' ); ?></label>
        <input class="podlove_subscribe_button_color" id="<?php echo $this->get_field_id( 'color' ); ?>" name="<?php echo $this->get_field_name( 'color' ); ?>" value="<?php echo esc_attr($color); ?>" />
        <style type="text/css">
            .sp-replacer {
                display: flex;
            }
            .sp-preview {
                flex-grow: 10;
            }
        </style>

        <label for="<?php echo $this->get_field_id( 'button' ); ?>"><?php _e( 'Button', 'podlove-subscribe-button' ); ?></label>
        <select class="widefat" id="<?php echo $this->get_field_id( 'button' ); ?>"
                name="<?php echo $this->get_field_name( 'button' ); ?>">
            <?php if ( isset($network_buttons) && count($network_buttons) > 0 ) : ?>
                <optgroup label="<?php _e('Local', 'podlove'); ?>">
                    <?php
                    foreach ($buttons as $subscribebutton) {
                        echo "<option value='" . sanitize_title($subscribebutton->name) . "' " . selected( sanitize_title($subscribebutton->name), $button ) . " >" . sanitize_title($subscribebutton->title) . " (" . sanitize_title($subscribebutton->name) . ")</option>";
                    }
                    ?>
                </optgroup>
                <optgroup label="<?php _e('Network', 'podlove'); ?>">
                    <?php
                    foreach ($network_buttons as $subscribebutton) {
                        echo "<option value='" . sanitize_title($subscribebutton->name) . "' " . selected( sanitize_title($subscribebutton->name), $button ) . " >" . sanitize_title($subscribebutton->title) . " (" . sanitize_title($subscribebutton->name) . ")</option>";
                    }
                    ?>
                </optgroup>
            <?php else :
                foreach ($buttons as $subscribebutton) {
                    echo "<option value='" . sanitize_title($subscribebutton->name) . "' " . selected( sanitize_title($subscribebutton->name), $button ) . " >" . sanitize_title($subscribebutton->title) . " (" . sanitize_title($subscribebutton->name) . ")</option>";
                }
            endif; ?>
        </select>

        <?php
        $customize_options = array(
            'size'      => array(
                'name'    => __( 'Size', 'podlove-subscribe-button' ),
                'options' => \PodloveSubscribeButton\Model\Button::$size
            ),
            'style'     => array(
                'name'    => __( 'Style', 'podlove-subscribe-button' ),
                'options' => \PodloveSubscribeButton\Model\Button::$style
            ),
            'format'    => array(
                'name'    => __( 'Format', 'podlove-subscribe-button' ),
                'options' => \PodloveSubscribeButton\Model\Button::$format
            ),
            'autowidth' => array(
                'name'    => __( 'Autowidth', 'podlove-subscribe-button' ),
                'options' => \PodloveSubscribeButton\Model\Button::$width
            )
        );

        foreach ($customize_options as $slug => $properties) : ?>
            <label for="<?php echo $this->get_field_id( $slug ); ?>"><?php echo $properties['name']; ?></label>
            <select class="widefat" id="<?php echo $this->get_field_id( $slug ); ?>" name="<?php echo $this->get_field_name( $slug ); ?>">
                <option value="default" <?php echo ( $$slug == 'default' ? 'selected="selected"' : '' ); ?>><?php printf( __( 'Default %s', 'podlove-subscribe-button' ), $properties['name'] ) ?></option>
                <optgroup>
                    <?php foreach ( $properties['options'] as $property => $name ) : ?>
                    <option value="<?php echo $property; ?>" <?php echo ( $$slug == $property ? 'selected="selected"' : '' ); ?>><?php echo $name; ?></option>
                    <?php endforeach; ?>
                </optgroup>
            </select>
        <?php endforeach; ?>

        <label for="<?php echo $this->get_field_id( 'infotext' ); ?>"><?php _e( 'Description', 'podlove-subscribe-button' ); ?></label>
        <textarea class="widefat" rows="10" id="<?php echo $this->get_field_id( 'infotext' ); ?>" name="<?php echo $this->get_field_name( 'infotext' ); ?>"><?php echo $infotext; ?></textarea>
    </p>
    <?php
}
// -x-
public function update( $new_instance, $old_instance ) {
    $instance = array();

    foreach (self::$widget_settings as $setting) {
        $instance[$setting]  = ( ! empty( $new_instance[$setting] ) ) ? strip_tags( $new_instance[$setting] ) : '';
    }

    return $instance;
}
// -x-

if( ! class_exists( 'WP_List_Table' ) ){
    require_once( ABSPATH . 'wp-admin/includes/class-wp-list-table.php' );
}
// -x-

function __construct(){
    global $status, $page;

    // Set parent defaults
    parent::__construct( array(
        'singular'  => 'feed',   // singular name of the listed records
        'plural'    => 'feeds',  // plural name of the listed records
        'ajax'      => false  // does this table support ajax?
    ) );
}
// -x-
function column_name( $button ) {

    $actions = array(
        'edit'   => Settings\Buttons::get_action_link( $button, __( 'Edit', 'podlove-subscribe-button' ), 'edit' ),
        'delete' => Settings\Buttons::get_action_link( $button, __( 'Delete', 'podlove-subscribe-button' ), 'confirm_delete' )
    );

    return sprintf('%1$s %2$s',
        /*$1%s*/ sanitize_title($button->title) . '<br><code>[podlove-subscribe-button button="' . sanitize_text_field($button->name) . '"]</code>',
        /*$3%s*/ $this->row_actions( $actions )
    );
}
// -x-
function column_button_preview( $button ) {

    if ( ! $button->feeds ) {
        return '<code>' . __( 'No preview. Please set a feed.', 'podlove-subscribe-button' ) . '</code>';
    } else {

        $preview = "<div class='podlove-button-preview-container'>";
        $preview .= $button->render(
            'big',
            'false',
            get_option( 'podlove_subscribe_button_default_style', 'filled' ),
            'rectangle'
        );
        $preview .= "</div>";

        return $preview;

    }

}
// -x-

function column_id( $button ) {
    return $button->id;
}
// -x-
function get_columns(){
    return array(
        'name'    => __( 'Title & Shortcode', 'podlove-subscribe-button' ),
        'button_preview'    => __( 'Preview', 'podlove-subscribe-button' ),
    );
}
// -x-
function prepare_items() {
    // number of items per page
    $per_page = 1000;

    // define column headers
    $columns = $this->get_columns();
    $hidden = array();
    $sortable = $this->get_sortable_columns();
    $this->_column_headers = array( $columns, $hidden, $sortable );

    // retrieve data
    // TODO select data for current page only
    $data = ( is_network_admin() ? \PodloveSubscribeButton\Model\NetworkButton::all() : \PodloveSubscribeButton\Model\Button::all() );

    // get current page
    $current_page = $this->get_pagenum();
    // get total items
    $total_items = count( $data );
    // extrage page for current page only
    $data = array_slice( $data, ( ( $current_page - 1 ) * $per_page ) , $per_page );
    // add items to table
    $this->items = $data;

    // register pagination options & calculations
    $this->set_pagination_args( array(
        'total_items' => $total_items,
        'per_page'    => $per_page,
        'total_pages' => ceil( $total_items / $per_page )
    ) );
}
// -x-
namespace PodloveSubscribeButton;

if( ! class_exists( 'WP_List_Table' ) ){
    require_once( ABSPATH . 'wp-admin/includes/class-wp-list-table.php' );
}
// -x-
// -x-
function __construct(){
    global $status, $page;

    // Set parent defaults
    parent::__construct( array(
        'singular'  => 'feed',   // singular name of the listed records
        'plural'    => 'feeds',  // plural name of the listed records
        'ajax'      => false  // does this table support ajax?
    ) );
}
// -x-
function column_name( $button ) {

    $actions = array(
        'edit'   => Settings\Buttons::get_action_link( $button, __( 'Edit', 'podlove-subscribe-button' ), 'edit' ),
        'delete' => Settings\Buttons::get_action_link( $button, __( 'Delete', 'podlove-subscribe-button' ), 'confirm_delete' )
    );

    return sprintf('%1$s %2$s',
        /*$1%s*/ sanitize_title($button->title) . '<br><code>[podlove-subscribe-button button="' . sanitize_text_field($button->name) . '"]</code>',
        /*$3%s*/ $this->row_actions( $actions )
    );
}
// -x-
function column_button_preview( $button ) {

    if ( ! $button->feeds ) {
        return '<code>' . __( 'No preview. Please set a feed.', 'podlove-subscribe-button' ) . '</code>';
    } else {

        $preview = "<div class='podlove-button-preview-container'>";
        $preview .= $button->render(
            'big',
            'false',
            get_option( 'podlove_subscribe_button_default_style', 'filled' ),
            'rectangle'
        );
        $preview .= "</div>";

        return $preview;

    }

}
// -x-

function column_id( $button ) {
    return $button->id;
}
// -x-
function get_columns(){
    return array(
        'name'    => __( 'Title & Shortcode', 'podlove-subscribe-button' ),
        'button_preview'    => __( 'Preview', 'podlove-subscribe-button' ),
    );
}
// -x-
function prepare_items() {
    // number of items per page
    $per_page = 1000;

    // define column headers
    $columns = $this->get_columns();
    $hidden = array();
    $sortable = $this->get_sortable_columns();
    $this->_column_headers = array( $columns, $hidden, $sortable );

    // retrieve data
    // TODO select data for current page only
    $data = ( is_network_admin() ? \PodloveSubscribeButton\Model\NetworkButton::all() : \PodloveSubscribeButton\Model\Button::all() );

    // get current page
    $current_page = $this->get_pagenum();
    // get total items
    $total_items = count( $data );
    // extrage page for current page only
    $data = array_slice( $data, ( ( $current_page - 1 ) * $per_page ) , $per_page );
    // add items to table
    $this->items = $data;

    // register pagination options & calculations
    $this->set_pagination_args( array(
        'total_items' => $total_items,
        'per_page'    => $per_page,
        'total_pages' => ceil( $total_items / $per_page )
    ) );
}
// -x-