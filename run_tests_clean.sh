#!/bin/bash
set -e

echo "=========================================="
echo "Clean Test Execution"
echo "=========================================="
echo ""

echo "1. Stopping containers..."
docker-compose down --remove-orphans 2>&1 | grep -v "warning msg"

echo ""
echo "2. Building API container..."
docker-compose build api 2>&1 | grep -E "(Step|Successfully built|Built)" | tail -5

echo ""
echo "3. Starting services..."
docker-compose up -d 2>&1 | grep -v "warning msg"

echo ""
echo "4. Waiting for services to be ready..."
sleep 10

echo ""
echo "5. Running tests..."
docker-compose exec -T api pytest tests/ -v --tb=short --maxfail=3

echo ""
echo "=========================================="
echo "Tests completed!"
echo "=========================================="
