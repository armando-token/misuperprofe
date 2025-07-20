#!/bin/bash

API_URL="http://localhost:8000"
API_KEY="Tecsup1983101459"
USER_ID="demo"

RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m' # No Color

function test_endpoint() {
  local name="$1"
  local cmd="$2"
  echo -n "Probando $name... "
  eval "$cmd" > /dev/null 2>&1
  if [ $? -eq 0 ]; then
    echo -e "${GREEN}OK${NC}"
  else
    echo -e "${RED}FAIL${NC}"
  fi
}

test_endpoint "/health" "curl -s -f $API_URL/health"
test_endpoint "/ask" "curl -s -f -X POST $API_URL/ask -H 'Authorization: Bearer $API_KEY' -H 'Content-Type: application/json' -d '{\"pregunta\": \"que es biologia\"}'"
test_endpoint "/user_stats" "curl -s -f -X GET '$API_URL/user_stats?user_id=$USER_ID' -H 'Authorization: Bearer $API_KEY'"

echo "Pruebas finalizadas." 