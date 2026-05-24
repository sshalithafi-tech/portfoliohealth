#!/bin/bash

# Business Model Context Card - Comprehensive Test Script
# Tests all 5 business model values

ASSESSMENT_ID="6a1325ce6fe46ca1fb550732"

echo "================================================================================"
echo "BUSINESS MODEL CONTEXT CARD - COMPREHENSIVE TEST"
echo "================================================================================"
echo ""

# Test cases
declare -a VALUES=("ETO" "CETO" "CTO" "Standard" "Bulk")

for VALUE in "${VALUES[@]}"; do
    echo "================================================================================"
    echo "Testing business_model = '$VALUE'"
    echo "================================================================================"
    echo ""
    
    # Update MongoDB
    echo "[1/2] Updating MongoDB..."
    cd /app/backend && python3 -c "
import asyncio, os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
load_dotenv()
async def main():
    c = AsyncIOMotorClient(os.environ['MONGO_URL'])
    db = c[os.environ.get('DB_NAME','test_database')]
    result = await db.assessments.update_one(
        {'_id': '$ASSESSMENT_ID'},
        {'\$set': {'business_model': '$VALUE'}}
    )
    doc = await db.assessments.find_one({'_id': '$ASSESSMENT_ID'})
    print(f'✅ Updated: business_model = {doc.get(\"business_model\")}')
    c.close()
asyncio.run(main())
"
    
    echo ""
    echo "[2/2] Verifying UI (manual step required)"
    echo "  Navigate to: https://section-search.preview.emergentagent.com/assessments/$ASSESSMENT_ID/report"
    echo "  Check Business Model Context card for:"
    echo "    - Badge: $VALUE"
    echo "    - Description starts with expected text"
    echo ""
    
    # Pause between tests
    sleep 2
done

echo "================================================================================"
echo "ALL TESTS COMPLETE"
echo "================================================================================"
echo ""
echo "To reset business_model field:"
echo "cd /app/backend && python3 -c \""
echo "import asyncio, os"
echo "from motor.motor_asyncio import AsyncIOMotorClient"
echo "from dotenv import load_dotenv"
echo "load_dotenv()"
echo "async def main():"
echo "    c = AsyncIOMotorClient(os.environ['MONGO_URL'])"
echo "    db = c[os.environ.get('DB_NAME','test_database')]"
echo "    await db.assessments.update_one("
echo "        {'_id': '$ASSESSMENT_ID'},"
echo "        {'\\\$unset': {'business_model': ''}}"
echo "    )"
echo "    c.close()"
echo "asyncio.run(main())"
echo "\""
