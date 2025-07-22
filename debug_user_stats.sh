#!/bin/bash

# Script de diagnóstico para user_stats
API_BASE_URL="https://app.misuperprofe.com"
API_KEY="your_api_key_here"
USER_ID="usuario@example.com"

echo "🔍 DIAGNÓSTICO DE USER_STATS"
echo "=================================================="

# Generar el hash del usuario (simulado)
echo "User ID: $USER_ID"
echo "User ID Hash: $(echo -n "$USER_ID" | sha256sum | cut -d' ' -f1)"
echo

# Probar el endpoint user_stats
echo "📡 Llamando a user_stats..."
response=$(curl -s -w "\n%{http_code}" -X GET "$API_BASE_URL/api/v1/user_stats?user_id=$USER_ID" \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json")

# Separar respuesta y código de estado
http_code=$(echo "$response" | tail -n1)
response_body=$(echo "$response" | head -n -1)

echo "Status Code: $http_code"
echo

if [ "$http_code" = "200" ]; then
    echo "✅ Respuesta exitosa:"
    echo "$response_body" | jq '.' 2>/dev/null || echo "$response_body"
    
    # Análisis de los datos
    cursos_count=$(echo "$response_body" | jq '.resumen_por_curso | length' 2>/dev/null || echo "0")
    echo
    echo "📊 Análisis:"
    echo "Total de cursos con actividad: $cursos_count"
    
    # Mostrar detalles de cada curso
    echo "$response_body" | jq -r '.resumen_por_curso[] | "  - \(.curso): \(.total_intentos) intentos, \(.aciertos) aciertos"' 2>/dev/null || echo "No se pueden parsear los datos"
    
    ultimos_count=$(echo "$response_body" | jq '.ultimos_intentos | length' 2>/dev/null || echo "0")
    echo "Últimos intentos: $ultimos_count"
    
else
    echo "❌ Error: $http_code"
    echo "Error details: $response_body"
fi

echo
echo "🧪 PRUEBA DE LOG_RESULT"
echo "=================================================="

# Probar log_result con historia
test_data='{
  "user_id": "'$USER_ID'",
  "question_id": "test_debug_001",
  "answer": "A",
  "is_correct": true,
  "course": "historia",
  "topic": "Test Debug"
}'

echo "📡 Enviando log_result para curso: historia..."
log_response=$(curl -s -w "\n%{http_code}" -X POST "$API_BASE_URL/api/v1/log_result" \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d "$test_data")

log_http_code=$(echo "$log_response" | tail -n1)
log_response_body=$(echo "$log_response" | head -n -1)

echo "Status Code: $log_http_code"

if [ "$log_http_code" = "200" ]; then
    echo "✅ Log_result exitoso"
    echo
    echo "🔄 Verificando user_stats después del log..."
    sleep 2
    
    # Verificar user_stats nuevamente
    new_response=$(curl -s -w "\n%{http_code}" -X GET "$API_BASE_URL/api/v1/user_stats?user_id=$USER_ID" \
      -H "Authorization: Bearer $API_KEY" \
      -H "Content-Type: application/json")
    
    new_http_code=$(echo "$new_response" | tail -n1)
    new_response_body=$(echo "$new_response" | head -n -1)
    
    echo "Status Code: $new_http_code"
    
    if [ "$new_http_code" = "200" ]; then
        new_cursos_count=$(echo "$new_response_body" | jq '.resumen_por_curso | length' 2>/dev/null || echo "0")
        echo "Total de cursos después del log: $new_cursos_count"
        
        # Verificar si aparece historia
        historia_count=$(echo "$new_response_body" | jq '.resumen_por_curso[] | select(.curso == "historia") | .total_intentos' 2>/dev/null || echo "0")
        echo "Intentos en historia: $historia_count"
        
        if [ "$historia_count" != "0" ] && [ "$historia_count" != "null" ]; then
            echo "✅ Historia aparece correctamente en user_stats"
        else
            echo "❌ Historia NO aparece en user_stats"
        fi
    fi
else
    echo "❌ Error en log_result: $log_http_code"
    echo "Error details: $log_response_body"
fi

echo
echo "🔍 DIAGNÓSTICO COMPLETO"
echo "==================================================" 