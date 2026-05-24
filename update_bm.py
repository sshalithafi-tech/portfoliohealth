#!/usr/bin/env python3
"""
Update business_model field for testing
Usage: python3 update_bm.py <value>
       python3 update_bm.py --reset
"""

import asyncio
import os
import sys
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId
from dotenv import load_dotenv

load_dotenv('/app/backend/.env')

ASSESSMENT_ID = '6a1325ce6fe46ca1fb550732'

async def update_business_model(value):
    c = AsyncIOMotorClient(os.environ['MONGO_URL'])
    db = c[os.environ.get('DB_NAME','test_database')]
    
    result = await db.assessments.update_one(
        {'_id': ObjectId(ASSESSMENT_ID)},
        {'$set': {'business_model': value}}
    )
    
    # Verify
    doc = await db.assessments.find_one({'_id': ObjectId(ASSESSMENT_ID)})
    current = doc.get('business_model') if doc else None
    
    c.close()
    return current

async def reset_business_model():
    c = AsyncIOMotorClient(os.environ['MONGO_URL'])
    db = c[os.environ.get('DB_NAME','test_database')]
    
    result = await db.assessments.update_one(
        {'_id': ObjectId(ASSESSMENT_ID)},
        {'$unset': {'business_model': ''}}
    )
    
    c.close()
    return result.modified_count > 0

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 update_bm.py <value>")
        print("       python3 update_bm.py --reset")
        sys.exit(1)
    
    if sys.argv[1] == "--reset":
        success = asyncio.run(reset_business_model())
        if success:
            print("✅ business_model field reset")
        else:
            print("❌ Failed to reset")
    else:
        value = sys.argv[1]
        current = asyncio.run(update_business_model(value))
        if current == value:
            print(f"✅ business_model = '{current}'")
        else:
            print(f"❌ Failed: expected '{value}', got '{current}'")
