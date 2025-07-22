#!/bin/bash

# Script para recrear datos de prueba en varios cursos
API_BASE_URL="https://app.misuperprofe.com"
API_KEY="your_api_key_here"
USER_ID="usuario@example.com"

echo "🔄 RECREANDO DATOS DE PRUEBA"
echo "=================================================="

# Lista de cursos para probar
cursos=("biologia" "historia" "geografia" "filosofia" "literatura" "economia" "civica" "psicologia")

# Función para enviar log_result
send_log_result() {
    local course=$1
    local topic=$2
    local question_id=$3
    local answer=$4
    local is_correct=$5
    
    local test_data='{
      "user_id": "'$USER_ID'",
      "question_id": "'$question_id'",
      "answer": "'$answer'",
      "is_correct": '$is_correct',
      "course": "'$course'",
      "topic": "'$topic'"
    }'
    
    response=$(curl -s -w "\n%{http_code}" -X POST "$API_BASE_URL/api/v1/log_result" \
      -H "Authorization: Bearer $API_KEY" \
      -H "Content-Type: application/json" \
      -d "$test_data")
    
    http_code=$(echo "$response" | tail -n1)
    
    if [ "$http_code" = "200" ]; then
        echo "✅ $course - $topic: $answer ($is_correct)"
    else
        echo "❌ $course - $topic: Error $http_code"
    fi
}

# Enviar datos de prueba para cada curso
for curso in "${cursos[@]}"; do
    echo
    echo "📚 Agregando datos para: $curso"
    echo "----------------------------------------"
    
    # Enviar 3-4 intentos por curso
    case $curso in
        "biologia")
            send_log_result "$curso" "Célula animal" "bio_001" "A" true
            send_log_result "$curso" "Fotosíntesis" "bio_002" "B" false
            send_log_result "$curso" "ADN" "bio_003" "C" true
            send_log_result "$curso" "Evolución" "bio_004" "D" true
            ;;
        "historia")
            send_log_result "$curso" "Revolución Francesa" "hist_001" "A" true
            send_log_result "$curso" "Segunda Guerra Mundial" "hist_002" "B" true
            send_log_result "$curso" "Independencia de América" "hist_003" "C" false
            ;;
        "geografia")
            send_log_result "$curso" "Capitales de Europa" "geo_001" "A" true
            send_log_result "$curso" "Climas del mundo" "geo_002" "B" false
            send_log_result "$curso" "Relieve terrestre" "geo_003" "C" true
            ;;
        "filosofia")
            send_log_result "$curso" "Platón" "fil_001" "A" true
            send_log_result "$curso" "Aristóteles" "fil_002" "B" true
            send_log_result "$curso" "Descartes" "fil_003" "C" false
            ;;
        "literatura")
            send_log_result "$curso" "Don Quijote" "lit_001" "A" true
            send_log_result "$curso" "Cien años de soledad" "lit_002" "B" false
            send_log_result "$curso" "Poesía romántica" "lit_003" "C" true
            ;;
        "economia")
            send_log_result "$curso" "Oferta y demanda" "eco_001" "A" true
            send_log_result "$curso" "PIB" "eco_002" "B" true
            send_log_result "$curso" "Inflación" "eco_003" "C" false
            ;;
        "civica")
            send_log_result "$curso" "Derechos humanos" "civ_001" "A" true
            send_log_result "$curso" "Constitución" "civ_002" "B" false
            send_log_result "$curso" "Democracia" "civ_003" "C" true
            ;;
        "psicologia")
            send_log_result "$curso" "Psicoanálisis" "psi_001" "A" true
            send_log_result "$curso" "Conductismo" "psi_002" "B" true
            send_log_result "$curso" "Cognitivismo" "psi_003" "C" false
            ;;
    esac
    
    sleep 1  # Pausa entre cursos
done

echo
echo "✅ DATOS DE PRUEBA RECREADOS"
echo "=================================================="
echo "Ahora ejecuta: ./debug_user_stats.sh"
echo "para verificar que aparecen todos los cursos" 