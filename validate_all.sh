#!/bin/bash
# Validation script - Run all tests cleanly

set -e

echo "=============================================="
echo "PDF-to-Markdown Extractor - Test Validation"
echo "=============================================="
echo ""

echo "Step 1/5: Stopping existing containers..."
docker-compose down 2>&1 | grep -v "warning msg" || true
echo "✅ Containers stopped"
echo ""

echo "Step 2/5: Building API container..."
docker-compose build api 2>&1 | grep -E "Successfully built|Built" | tail -1
echo "✅ Container built"
echo ""

echo "Step 3/5: Starting services..."
docker-compose up -d 2>&1 | grep -v "warning msg"
echo "✅ Services started"
echo ""

echo "Step 4/5: Waiting for services to be ready (15s)..."
sleep 15
echo "✅ Services ready"
echo ""

echo "Step 5/5: Running all tests..."
echo "=============================================="
docker-compose exec -T api pytest tests/ -v --tb=short 2>&1 | tee test_results.log
echo "=============================================="
echo ""

# Summary
TOTAL=$(grep -c "PASSED\|FAILED\|SKIPPED" test_results.log || echo "0")
PASSED=$(grep -c "PASSED" test_results.log || echo "0")
FAILED=$(grep -c "FAILED" test_results.log || echo "0")
SKIPPED=$(grep -c "SKIPPED" test_results.log || echo "0")

echo "=============================================="
echo "TEST RESULTS SUMMARY"
echo "=============================================="
echo "Total tests : $TOTAL"
echo "✅ Passed   : $PASSED"
echo "❌ Failed   : $FAILED"
echo "⏭️  Skipped  : $SKIPPED"
echo "=============================================="
echo ""
echo "Full results saved to: test_results.log"
