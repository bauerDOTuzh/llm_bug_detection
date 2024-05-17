<?php
public static function find_one_by_property( $property, $value ) {
    global $wpdb;
    
    $class = get_called_class();
    $model = new $class();
    $model->flag_as_not_new();
    
    $row = $wpdb->get_row(
        'SELECT * FROM ' . static::table_name() . ' WHERE ' . $property .  ' = \'' . $value . '\' LIMIT 0,1'
    );
    
    if ( ! $row ) {
        return null;
    }
    
    foreach ( $row as $property => $value ) {
        $model->$property = static::unserialize_property($value);
    }
    
    return $model;
}