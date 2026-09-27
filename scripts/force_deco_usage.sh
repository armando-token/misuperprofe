#!/bin/bash

echo "🔧 FORZANDO USO DE DECO - ELIMINANDO /get_question COMPLETAMENTE"
echo "================================================================"

API_KEY="${API_KEY:-}"

# 1. Comentar endpoints /get_question
echo "📝 Comentando endpoints /get_question..."

# Comentar POST /get_question
sed -i 's/@chat_business_router.post("\/get_question"/# @chat_business_router.post("\/get_question"/' src/app/api/routers/chat_business_router.py

# Comentar GET /get_question  
sed -i 's/@log_router.get("\/get_question"/# @log_router.get("\/get_question"/' src/app/api/log.py

# 2. Reiniciar servidor
echo "🔄 Reiniciando servidor..."
./scripts/safe_restart.sh

# 3. Verificar que /get_question ya no aparece en OpenAPI
echo "🔍 Verificando OpenAPI schema..."
sleep 10

curl -s "http://localhost:8000/api/v1/agent/openapi.json" | jq '.paths | keys | map(select(contains("get_question")))' > /tmp/get_question_endpoints.json

if [ -s /tmp/get_question_endpoints.json ]; then
    echo "❌ ERROR: /get_question aún aparece en OpenAPI schema"
    cat /tmp/get_question_endpoints.json
else
    echo "✅ ÉXITO: /get_question eliminado del OpenAPI schema"
fi

# 4. Verificar que /deco/question sigue funcionando
echo "🔍 Verificando que /deco/question funciona..."
curl -X POST "http://localhost:8000/api/v1/deco/question" \
  -H "Authorization: Bearer ${API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{"user_id": "user@example.com", "area": "historia", "topic": "general", "difficulty": 2}' \
  | jq '.question' > /dev/null

if [ $? -eq 0 ]; then
    echo "✅ /deco/question funciona correctamente"
else
    echo "❌ ERROR: /deco/question no funciona"
fi

echo ""
echo "🎯 RESULTADO:"
echo "- /get_question eliminado del OpenAPI schema"
echo "- Custom GPT solo verá endpoints DECO"
echo "- Debe usar POST /deco/question obligatoriamente"
echo ""
echo "📋 PRÓXIMOS PASOS:"
echo "1. Reiniciar el Custom GPT"
echo "2. Probar con 'dame una pregunta'"
echo "3. Verificar que usa /deco/question" 