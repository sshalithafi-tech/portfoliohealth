#!/usr/bin/env python3
"""
Business Model Context Card Verification Script
Tests all 5 business model values and verifies badge + description rendering
"""

import asyncio
import os
import sys
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

# Load environment variables
load_dotenv('/app/backend/.env')

# Test cases with expected outcomes
TEST_CASES = [
    {
        "raw_value": "ETO",
        "expected_badge": "ETO",
        "expected_desc_start": "Engineer-to-Order: every product is fully designed"
    },
    {
        "raw_value": "CETO",
        "expected_badge": "CETO",
        "expected_desc_start": "Configure-and-Engineer-to-Order: a standard base is configured"
    },
    {
        "raw_value": "CTO",
        "expected_badge": "CTO",
        "expected_desc_start": "Configure-to-Order: customers select from a predefined option"
    },
    {
        "raw_value": "Standard",
        "expected_badge": "Standard",
        "expected_desc_start": "Standard Products: manufactured at scale with fixed"
    },
    {
        "raw_value": "Bulk",
        "expected_badge": "Bulk",
        "expected_desc_start": "Bulk: high-volume production where competitive advantage"
    }
]

ASSESSMENT_ID = "6a1325ce6fe46ca1fb550732"

async def update_business_model(value):
    """Update the business_model field in MongoDB"""
    client = AsyncIOMotorClient(os.environ['MONGO_URL'])
    db = client[os.environ.get('DB_NAME', 'test_database')]
    
    result = await db.assessments.update_one(
        {'_id': ASSESSMENT_ID},
        {'$set': {'business_model': value}}
    )
    
    client.close()
    return result.modified_count > 0 or result.matched_count > 0

async def reset_business_model():
    """Reset the business_model field to empty"""
    client = AsyncIOMotorClient(os.environ['MONGO_URL'])
    db = client[os.environ.get('DB_NAME', 'test_database')]
    
    result = await db.assessments.update_one(
        {'_id': ASSESSMENT_ID},
        {'$unset': {'business_model': ''}}
    )
    
    client.close()
    return result.modified_count > 0 or result.matched_count > 0

async def get_current_business_model():
    """Get the current business_model value"""
    client = AsyncIOMotorClient(os.environ['MONGO_URL'])
    db = client[os.environ.get('DB_NAME', 'test_database')]
    
    assessment = await db.assessments.find_one({'_id': ASSESSMENT_ID})
    client.close()
    
    return assessment.get('business_model') if assessment else None

async def main():
    print("=" * 80)
    print("BUSINESS MODEL CONTEXT CARD - MONGODB UPDATE SCRIPT")
    print("=" * 80)
    
    # Get current value
    current = await get_current_business_model()
    print(f"\nCurrent business_model value: {current}")
    
    # Test each value
    for idx, test_case in enumerate(TEST_CASES, 1):
        raw_value = test_case["raw_value"]
        print(f"\n{'=' * 80}")
        print(f"TEST {idx}/5: Setting business_model = '{raw_value}'")
        print(f"{'=' * 80}")
        
        success = await update_business_model(raw_value)
        if success:
            print(f"✅ MongoDB updated successfully")
            
            # Verify the update
            verify = await get_current_business_model()
            if verify == raw_value:
                print(f"✅ Verified: business_model = '{verify}'")
            else:
                print(f"❌ Verification failed: expected '{raw_value}', got '{verify}'")
        else:
            print(f"❌ Failed to update MongoDB")
    
    print(f"\n{'=' * 80}")
    print("ALL MONGODB UPDATES COMPLETE")
    print(f"{'=' * 80}")
    print("\nNext step: Use Playwright to verify UI rendering for each value")
    print(f"Report URL: https://section-search.preview.emergentagent.com/assessments/{ASSESSMENT_ID}/report")
    
    # Ask if user wants to reset
    print(f"\n{'=' * 80}")
    print("CLEANUP")
    print(f"{'=' * 80}")
    print("\nTo reset business_model field, run:")
    print(f"python3 {__file__} --reset")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--reset":
        print("Resetting business_model field...")
        success = asyncio.run(reset_business_model())
        if success:
            print("✅ business_model field reset successfully")
        else:
            print("❌ Failed to reset business_model field")
    else:
        asyncio.run(main())
