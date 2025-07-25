#!/bin/bash

# Script para deshabilitar temporalmente el endpoint /get_question
# para forzar al Custom GPT a usar DECO

echo "🚨 Deshabilitando endpoint /get_question temporalmente..."
echo "=================================================="

# Crear backup de los archivos
cp src/app/api/routers/chat_business_router.py src/app/api/routers/chat_business_router_backup.py
cp src/app/api/log.py src/app/api/log_backup.py

echo "✅ Backups creados"

# Comentar el endpoint POST en chat_business_router.py
sed -i 's/@chat_business_router.post("\/get_question"/# @chat_business_router.post("\/get_question"/' src/app/api/routers/chat_business_router.py

# Comentar el endpoint GET en log.py
sed -i 's/@log_router.get("\/get_question")/# @log_router.get("\/get_question")/' src/app/api/log.py

echo "✅ Endpoints /get_question comentados"

# Reiniciar servidor
echo "🔄 Reiniciando servidor..."
./scripts/safe_restart.sh

echo "✅ Servidor reiniciado"
echo "🔍 Verificando que /get_question ya no esté disponible..."

# Verificar que el endpoint ya no esté en el OpenAPI schema
sleep 10
curl -s http://localhost:8000/api/v1/agent/openapi.json | jq '.paths | keys' | grep -E "(get_question|deco)" || echo "✅ /get_question eliminado del schema"

echo "=================================================="
echo "🎯 Ahora el Custom GPT SOLO verá /deco/question"
echo "💡 Para restaurar: ./scripts/restore_get_question_endpoint.sh" 