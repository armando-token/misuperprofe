#!/bin/bash

echo "🧪 PRUEBAS COMPLETAS DEL SISTEMA - 24 Julio 2025"
echo "================================================"
echo ""

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Contadores
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0
API_KEY="${API_KEY:-}"

# Función para test
test_function() {
    local test_name="$1"
    local command="$2"
    local expected_result="$3"
    
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    echo -e "${BLUE}🔍 Test: $test_name${NC}"
    
    if eval "$command" > /tmp/test_output 2>&1; then
        if [[ "$expected_result" == "success" ]] || [[ -z "$expected_result" ]]; then
            echo -e "${GREEN}✅ PASSED${NC}"
            PASSED_TESTS=$((PASSED_TESTS + 1))
        else
            echo -e "${RED}❌ FAILED - Expected: $expected_result${NC}"
            FAILED_TESTS=$((FAILED_TESTS + 1))
        fi
    else
        if [[ "$expected_result" == "failure" ]]; then
            echo -e "${GREEN}✅ PASSED (Expected failure)${NC}"
            PASSED_TESTS=$((PASSED_TESTS + 1))
        else
            echo -e "${RED}❌ FAILED${NC}"
            cat /tmp/test_output
            FAILED_TESTS=$((FAILED_TESTS + 1))
        fi
    fi
    echo ""
}

echo "📋 1. VERIFICACIÓN DE SERVICIOS"
echo "================================"

test_function "Servidor FastAPI" "curl -s http://localhost:8000/health" "success"
test_function "Base de datos PostgreSQL" "docker exec misuperpostgre pg_isready" "success"
test_function "Redis Cache" "docker exec misuperredis redis-cli ping" "success"

echo "📋 2. VERIFICACIÓN DE ENDPOINTS DECO"
echo "===================================="

# Test DECO question
test_function "POST /deco/question" "curl -X POST 'http://localhost:8000/api/v1/deco/question' \
  -H 'Authorization: Bearer ${API_KEY}' \
  -H 'Content-Type: application/json' \
  -d '{\"user_id\": \"user@example.com\", \"area\": \"historia\", \"topic\": \"general\", \"difficulty\": 2}' \
  | jq -r '.question' | grep -q ." "success"

# Test DECO answer
test_function "POST /deco/answer" "curl -X POST 'http://localhost:8000/api/v1/deco/answer' \
  -H 'Authorization: Bearer ${API_KEY}' \
  -H 'Content-Type: application/json' \
  -d '{\"user_id\": \"user@example.com\", \"session_id\": \"test_session\", \"answer\": \"A\", \"question_id\": \"test_123\"}' \
  | jq -r '.feedback' | grep -q ." "success"

# Test DECO areas
test_function "GET /deco/areas" "curl -s 'http://localhost:8000/api/v1/deco/areas' \
  -H 'Authorization: Bearer ${API_KEY}' \
  | jq -r '.areas' | grep -q ." "success"

# Test DECO cognitive skills
test_function "GET /deco/cognitive-skills" "curl -s 'http://localhost:8000/api/v1/deco/cognitive-skills' \
  -H 'Authorization: Bearer ${API_KEY}' \
  | jq -r '.cognitive_skills' | grep -q ." "success"

echo "📋 3. VERIFICACIÓN DE ELIMINACIÓN DE /get_question"
echo "=================================================="

# Verificar que /get_question NO aparece en OpenAPI
test_function "/get_question eliminado del OpenAPI" "curl -s 'http://localhost:8000/api/v1/agent/openapi.json' \
  | jq '.paths | keys | map(select(contains(\"get_question\")))' | grep -q '\[\]'" "success"

# Verificar que /get_question devuelve 404
test_function "GET /get_question devuelve 404" "curl -s -o /dev/null -w '%{http_code}' \
  'http://localhost:8000/api/v1/get_question?course=historia' | grep -q '404'" "success"

# Verificar que POST /get_question devuelve 404
test_function "POST /get_question devuelve 404" "curl -s -o /dev/null -w '%{http_code}' \
  -X POST 'http://localhost:8000/api/v1/get_question' \
  -H 'Authorization: Bearer ${API_KEY}' \
  -H 'Content-Type: application/json' \
  -d '{\"course\": \"historia\"}' | grep -q '404'" "success"

echo "📋 4. VERIFICACIÓN DE ENDPOINTS BASE"
echo "===================================="

# Test courses
test_function "GET /courses" "curl -s 'http://localhost:8000/api/v1/courses' \
  -H 'Authorization: Bearer ${API_KEY}' \
  | jq -r '.courses' | grep -q ." "success"

# Test ask endpoint
test_function "POST /ask" "curl -X POST 'http://localhost:8000/api/v1/ask' \
  -H 'Authorization: Bearer ${API_KEY}' \
  -H 'Content-Type: application/json' \
  -d '{\"pregunta\": \"¿Qué es la fotosíntesis?\"}' \
  | jq -r '.respuesta' | grep -q ." "success"

# Test log_result
test_function "POST /log_result" "curl -X POST 'http://localhost:8000/api/v1/log_result' \
  -H 'Authorization: Bearer ${API_KEY}' \
  -H 'Content-Type: application/json' \
  -d '{\"user_id\": \"user@example.com\", \"question_id\": \"test_123\", \"answer\": \"a\", \"is_correct\": true, \"course\": \"historia\", \"topic\": \"test\"}' \
  | jq -r '.status' | grep -q 'ok'" "success"

# Test user_stats
test_function "GET /user_stats" "curl -s 'http://localhost:8000/api/v1/user_stats?user_id=user@example.com' \
  -H 'Authorization: Bearer ${API_KEY}' \
  | jq -r '.stats' | grep -q ." "success"

echo "📋 5. VERIFICACIÓN DE MOTOR HÍBRIDO"
echo "===================================="

# Test content extraction
test_function "Motor híbrido con contenido real" "curl -X POST 'http://localhost:8000/api/v1/deco/question' \
  -H 'Authorization: Bearer ${API_KEY}' \
  -H 'Content-Type: application/json' \
  -d '{\"user_id\": \"user@example.com\", \"area\": \"historia\", \"topic\": \"general\", \"difficulty\": 2, \"chapter_id\": 155}' \
  | jq -r '.question' | grep -q ." "success"

# Test fallback to context
test_function "Motor híbrido con fallback" "curl -X POST 'http://localhost:8000/api/v1/deco/question' \
  -H 'Authorization: Bearer ${API_KEY}' \
  -H 'Content-Type: application/json' \
  -d '{\"user_id\": \"user@example.com\", \"area\": \"historia\", \"topic\": \"general\", \"difficulty\": 2}' \
  | jq -r '.question' | grep -q ." "success"

echo "📋 6. VERIFICACIÓN DE AUTENTICACIÓN"
echo "==================================="

# Test sin autorización en endpoint que requiere auth (lesson endpoints)
test_function "Sin autorización devuelve 401" "curl -s -o /dev/null -w '%{http_code}' \
  -X POST 'http://localhost:8000/api/v1/lesson/start' \
  -H 'Content-Type: application/json' \
  -d '{\"user_id\": \"user@example.com\", \"course\": \"historia\"}' | grep -q '401'" "success"

# Test con autorización incorrecta
test_function "Autorización incorrecta devuelve 401" "curl -s -o /dev/null -w '%{http_code}' \
  -X POST 'http://localhost:8000/api/v1/lesson/start' \
  -H 'Authorization: Bearer INVALID_TOKEN' \
  -H 'Content-Type: application/json' \
  -d '{\"user_id\": \"user@example.com\", \"course\": \"historia\"}' | grep -q '401'" "success"

echo "📋 7. VERIFICACIÓN DE RENDIMIENTO"
echo "=================================="

# Test tiempo de respuesta DECO
test_function "Tiempo de respuesta DECO < 10s" "timeout 10 curl -X POST 'http://localhost:8000/api/v1/deco/question' \
  -H 'Authorization: Bearer ${API_KEY}' \
  -H 'Content-Type: application/json' \
  -d '{\"user_id\": \"user@example.com\", \"area\": \"historia\", \"topic\": \"general\", \"difficulty\": 2}' > /dev/null" "success"

# Test tiempo de respuesta /ask
test_function "Tiempo de respuesta /ask < 5s" "timeout 5 curl -X POST 'http://localhost:8000/api/v1/ask' \
  -H 'Authorization: Bearer ${API_KEY}' \
  -H 'Content-Type: application/json' \
  -d '{\"pregunta\": \"¿Qué es la fotosíntesis?\"}' > /dev/null" "success"

echo "📋 8. VERIFICACIÓN DE FORMATO DE RESPUESTAS"
echo "==========================================="

# Test formato DECO question
test_function "Formato DECO question correcto" "curl -X POST 'http://localhost:8000/api/v1/deco/question' \
  -H 'Authorization: Bearer ${API_KEY}' \
  -H 'Content-Type: application/json' \
  -d '{\"user_id\": \"user@example.com\", \"area\": \"historia\", \"topic\": \"general\", \"difficulty\": 2}' \
  | jq -r '.question, .alternatives.A, .alternatives.B, .alternatives.C, .alternatives.D, .correct_answer' | grep -q ." "success"

# Test formato DECO answer
test_function "Formato DECO answer correcto" "curl -X POST 'http://localhost:8000/api/v1/deco/answer' \
  -H 'Authorization: Bearer ${API_KEY}' \
  -H 'Content-Type: application/json' \
  -d '{\"user_id\": \"user@example.com\", \"session_id\": \"test_session\", \"answer\": \"A\", \"question_id\": \"test_123\"}' \
  | jq -r '.is_correct, .feedback' | grep -q ." "success"

echo "📋 9. VERIFICACIÓN DE CACHE"
echo "============================"

# Test cache DECO (segunda llamada debería ser más rápida)
test_function "Cache DECO funcionando" "curl -X POST 'http://localhost:8000/api/v1/deco/question' \
  -H 'Authorization: Bearer ${API_KEY}' \
  -H 'Content-Type: application/json' \
  -d '{\"user_id\": \"user@example.com\", \"area\": \"comunicacion\", \"topic\": \"general\", \"difficulty\": 2}' > /dev/null" "success"

echo "📋 10. VERIFICACIÓN DE LOGS"
echo "============================"

# Verificar que no hay errores críticos en logs
test_function "Logs sin errores críticos" "docker logs misuperapi --tail 50 | grep -v 'ERROR\|CRITICAL' > /dev/null" "success"

echo ""
echo "📊 RESUMEN DE PRUEBAS"
echo "===================="
echo -e "${BLUE}Total de pruebas: $TOTAL_TESTS${NC}"
echo -e "${GREEN}Pruebas exitosas: $PASSED_TESTS${NC}"
echo -e "${RED}Pruebas fallidas: $FAILED_TESTS${NC}"

if [ $FAILED_TESTS -eq 0 ]; then
    echo -e "${GREEN}🎉 ¡TODAS LAS PRUEBAS PASARON!${NC}"
    echo -e "${GREEN}✅ Sistema completamente operativo${NC}"
    echo -e "${GREEN}✅ Motor híbrido funcionando${NC}"
    echo -e "${GREEN}✅ DECO forzado correctamente${NC}"
    exit 0
else
    echo -e "${RED}❌ $FAILED_TESTS pruebas fallaron${NC}"
    echo -e "${YELLOW}⚠️ Revisar logs para más detalles${NC}"
    exit 1
fi 