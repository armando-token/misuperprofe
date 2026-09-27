#!/bin/bash

echo "🤖 Simulando request del Custom GPT..."
echo "=================================================="

# Simular el request que está enviando el Custom GPT
echo "📝 Simulando request con datos que podría estar enviando el Custom GPT:"

# Test 1: Con chapter_id (que no es parte del schema DECO)
echo "📝 Test 1: Con chapter_id (incorrecto para DECO)"
curl -X POST http://localhost:8000/api/v1/deco/question \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${API_KEY}" \
  -d '{"user_id": "user@example.com", "area": "literatura", "topic": "comunicacion", "chapter_id": 1027}' \
  -s | jq '.'

echo ""
echo "📝 Test 2: Con course en lugar de area"
curl -X POST http://localhost:8000/api/v1/deco/question \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${API_KEY}" \
  -d '{"user_id": "user@example.com", "course": "literatura", "topic": "comunicacion", "difficulty": 2}' \
  -s | jq '.'

echo ""
echo "📝 Test 3: Sin topic"
curl -X POST http://localhost:8000/api/v1/deco/question \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${API_KEY}" \
  -d '{"user_id": "user@example.com", "area": "literatura", "difficulty": 2}' \
  -s | jq '.'

echo ""
echo "📝 Test 4: Con difficulty como string"
curl -X POST http://localhost:8000/api/v1/deco/question \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${API_KEY}" \
  -d '{"user_id": "user@example.com", "area": "literatura", "topic": "comunicacion", "difficulty": "2"}' \
  -s | jq '.'

echo ""
echo "📝 Test 5: Con datos extra"
curl -X POST http://localhost:8000/api/v1/deco/question \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${API_KEY}" \
  -d '{"user_id": "user@example.com", "area": "literatura", "topic": "comunicacion", "difficulty": 2, "extra_field": "value"}' \
  -s | jq '.'

echo ""
echo "=================================================="
echo "✅ Tests completados" 