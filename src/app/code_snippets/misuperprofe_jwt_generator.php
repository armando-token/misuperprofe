<?php

// --- Carga de la librería PHP-JWT ---
$jwt_library_path = WP_CONTENT_DIR . '/libs/php-jwt/src/JWT.php';
$key_path = WP_CONTENT_DIR . '/libs/php-jwt/src/Key.php';

if (file_exists($jwt_library_path) && file_exists($key_path)) {
    require_once $jwt_library_path;
    require_once $key_path;
} else {
    error_log('Error crítico: Archivos JWT.php o Key.php de PHP-JWT no encontrados. El shortcode [misuperprofe_jwt_token] no funcionará.');
    return; // Detiene la ejecución
}

use Firebase\JWT\JWT;
use Firebase\JWT\Key;

function misuperprofe_generate_jwt_token_shortcode_function() {
    if ( !is_user_logged_in() ) {
        return '<!-- Usuario no autenticado en WordPress -->';
    }

    $current_user = wp_get_current_user();
    if ( !$current_user || $current_user->ID === 0 ) {
        return '<!-- No se pudieron obtener los datos del usuario de WordPress -->';
    }

    if ( !defined('MI_SUPERPROFE_JWT_SECRET_KEY') ) {
        error_log('Error: MI_SUPERPROFE_JWT_SECRET_KEY no está definida en wp-config.php.');
        return '<!-- Error de configuración: Clave secreta JWT no definida. -->';
    }
    $secret_key = MI_SUPERPROFE_JWT_SECRET_KEY;

    // --- Preparar el payload según el esquema TokenClaims de FastAPI ---
    $issued_at       = time();
    $expiration_time = $issued_at + (60 * 60); // Token válido por 1 hora
    $issuer          = get_site_url(); 
    $audience        = 'https://app.misuperprofe.com'; // Audiencia esperada por tu API

    $payload = array(
        'sub'                       => (string) $current_user->ID,
        'external_user_identifier'  => $current_user->user_email,
        'role'                      => 'alumno',
        'name'                      => $current_user->display_name,
        
        'iat'                       => $issued_at,
        'exp'                       => $expiration_time,
        'iss'                       => $issuer,
        'aud'                       => $audience,
    );

    try {
        if (!class_exists('Firebase\JWT\JWT') || !class_exists('Firebase\JWT\Key')) {
            error_log('Error: Clases JWT o Key no disponibles al intentar generar el token.');
            return '<!-- Error interno: Clases JWT no disponibles. -->';
        }
        $jwt = JWT::encode($payload, $secret_key, 'HS256');

        // Construir el iframe completo
        $chat_frontend_url = 'http://18.214.59.62:5174/'; // IP pública y puerto del frontend-chat
        $iframe_src = $chat_frontend_url . '?token=' . esc_attr($jwt);
        
        // Considerar añadir más atributos al iframe si es necesario (ej. width, height, style, frameborder)
        // Por ahora, un iframe básico. Asegúrate de que tu CSS maneje el tamaño.
        $iframe_html = '<iframe src="' . $iframe_src . '" width="100%" height="600px" style="border:none;"></iframe>';
        
        return $iframe_html;
    } catch (Throwable $e) {
        error_log('Error al generar el token JWT: ' . $e->getMessage() . ' en ' . $e->getFile() . ':' . $e->getLine());
        return '<!-- Error al generar el token. Revisa los logs. -->';
    }
}
add_shortcode('misuperprofe_jwt_token', 'misuperprofe_generate_jwt_token_shortcode_function');

?> 