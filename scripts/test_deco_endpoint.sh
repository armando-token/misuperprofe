#!/bin/bash

echo "🧪 Probando endpoint DECO con diferentes parámetros..."
echo "=================================================="

# Test 1: Parámetros básicos
echo "📝 Test 1: Parámetros básicos"
curl -X POST http://localhost:8000/api/v1/deco/question \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your_api_key_here" \
  -d '{"user_id": "user@example.com", "area": "literatura", "topic": "comunicacion", "difficulty": 2}' \
  -s | jq '.'

echo ""
echo "📝 Test 2: Sin user_id"
curl -X POST http://localhost:8000/api/v1/deco/question \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your_api_key_here" \
  -d '{"area": "literatura", "topic": "comunicacion", "difficulty": 2}' \
  -s | jq '.'

echo ""
echo "📝 Test 3: Con cognitive_skill"
curl -X POST http://localhost:8000/api/v1/deco/question \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your_api_key_here" \
  -d '{"user_id": "user@example.com", "area": "literatura", "topic": "comunicacion", "difficulty": 2, "cognitive_skill": "aplicacion"}' \
  -s | jq '.'

echo ""
echo "📝 Test 4: Datos mínimos"
curl -X POST http://localhost:8000/api/v1/deco/question \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your_api_key_here" \
  -d '{"user_id": "user@example.com", "area": "literatura", "topic": "comunicacion"}' \
  -s | jq '.'

echo ""
echo "=================================================="
echo "✅ Tests completados" 