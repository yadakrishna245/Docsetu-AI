#!/bin/bash
# Quick health check for DocSetu AI services

API_URL=${1:-"http://localhost:8000"}
FRONTEND_URL=${2:-"http://localhost:3000"}

echo "=== DocSetu AI Health Check ==="
echo ""

# Check API
echo -n "API ($API_URL/health): "
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$API_URL/health")
if [ "$HTTP_CODE" == "200" ]; then
    echo "✅ OK ($HTTP_CODE)"
else
    echo "❌ FAILED ($HTTP_CODE)"
fi

# Check Frontend
echo -n "Frontend ($FRONTEND_URL): "
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$FRONTEND_URL")
if [ "$HTTP_CODE" == "200" ]; then
    echo "✅ OK ($HTTP_CODE)"
else
    echo "❌ FAILED ($HTTP_CODE)"
fi

echo ""
echo "Done."
