<?php
/**
 * Plugin Name: MiSuperProfe Chat Auth Endpoint
 * Description: Provides a REST API endpoint to check WordPress user login status and Paid Memberships Pro active membership for the chat application. Relies on WordPress's built-in REST API authentication (e.g., Application Passwords).
 * Version: 2.0.0
 * Author: MiSuperProfe Team
 */

// Exit if accessed directly.
if ( ! defined( 'ABSPATH' ) ) {
    exit;
}

error_log('[MiSuperProfe Debug] Plugin misuperprofe-chat-auth-endpoint.php v2.0.0 cargado.');

/**
 * Registra el endpoint REST personalizado.
 */
function misuperprofe_register_auth_status_endpoint() {
    register_rest_route( 'misuperprofe/v1', '/auth_status', array( 'methods' => 'GET', 'callback' => 'misuperprofe_auth_status_callback', 'permission_callback' => '__return_true' ) );
    error_log('[MiSuperProfe Debug] Endpoint /auth_status registrado.');
}
add_action( 'rest_api_init', 'misuperprofe_register_auth_status_endpoint' );

/**
 * Callback para el endpoint REST.
 */
function misuperprofe_auth_status_callback( WP_REST_Request $request ) {
    error_log('[MiSuperProfe Debug] Endpoint /auth_status ALCANZADO.');
    // Ya no es necesario loguear $_COOKIE, la autenticación la maneja WP por Basic Auth.

    $user_logged_in = is_user_logged_in();
    $user_id = 0;
    $display_name = null;
    $member_active = false;

    error_log('[MiSuperProfe Debug] auth_status: is_user_logged_in() es ' . ($user_logged_in ? 'TRUE' : 'FALSE'));

    if ( $user_logged_in ) {
        $current_user = wp_get_current_user();
        $user_id = $current_user->ID;
        $display_name = $current_user->display_name;
        error_log('[MiSuperProfe Debug] auth_status: user_id es ' . $user_id);
        if ( function_exists( 'pmpro_hasMembershipLevel' ) ) {
            if ( pmpro_hasMembershipLevel( null, $user_id ) ) { $member_active = true; }
            error_log('[MiSuperProfe Debug] auth_status: pmpro_hasMembershipLevel() para user ' . $user_id . ' es ' . ($member_active ? 'TRUE' : 'FALSE'));
        } else {
            error_log('[MiSuperProfe Debug] auth_status: La función pmpro_hasMembershipLevel no existe.');
        }
    }
    return new WP_REST_Response( array( 'logged_in' => $user_logged_in, 'member_active'=> $member_active, 'user_id' => $user_id, 'display_name' => $display_name ), 200 );
}

/**
 * Filtro para asegurar que se envíen las cabeceras CORS correctas.
 */
add_filter( 'rest_pre_serve_request', function( $served, $result, $request, $server ) {
    // Asegurarse que la ruta coincide con el nuevo nombre del endpoint
    if ( strpos( $request->get_route(), '/misuperprofe/v1/auth_status' ) !== false ) {
        $origin = get_http_origin();
        if ( $origin ) {
            $allowed_origins = [ 'http://18.214.59.62:5174', 'http://localhost:5174', 'http://localhost:5175', 'http://localhost:5173' ];
            if ( in_array( $origin, $allowed_origins, true ) ) {
                header( 'Access-Control-Allow-Origin: ' . $origin );
                header( 'Access-Control-Allow-Credentials: true' ); // Importante para Basic Auth con fetch
            }
        }
        error_log('[MiSuperProfe Debug] Filtro rest_pre_serve_request: Origen: ' . ($origin ? $origin : "N/A") . '. Cabeceras CORS para /auth_status aplicadas (si el origen es permitido).');
    }
    return $served;
}, 10, 4 );

add_filter( 'rest_allowed_cors_origins', function ( $allowed_origins ) {
    $frontend_origins = [ 'http://18.214.59.62:5174', 'http://localhost:5175', 'http://localhost:5173' ]; 
    foreach ( $frontend_origins as $frontend_origin ) {
        if ( ! in_array( $frontend_origin, $allowed_origins ) ) {
            $allowed_origins[] = $frontend_origin;
        }
    }
    error_log('[MiSuperProfe Debug] Filtro rest_allowed_cors_origins: Orígenes permitidos actuales: ' . implode(', ', $allowed_origins));
    return $allowed_origins;
});

?>
