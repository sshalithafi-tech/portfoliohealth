"""Seed a completed assessment (Lumivex fixture) for the admin user so the
PDF + report endpoints can be exercised end-to-end by the testing agent."""
import asyncio
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent / ".env")

from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId
from datetime import datetime, timezone

from chat_service import normalise_report_weights
from tests.test_report_fixes import lumivex_report

FIXED_ID = "6b44c78c2ebdd66625059999"


async def main():
    client = AsyncIOMotorClient(os.environ["MONGO_URL"])
    db = client[os.environ["DB_NAME"]]
    admin = await db.users.find_one({"email": os.environ.get("ADMIN_EMAIL", "admin@portfoliohealth.fi")})
    if not admin:
        print("No admin user found"); return
    user_id = str(admin["_id"])

    company = await db.companies.find_one({"user_id": user_id, "name": "Lumivex Photonics"})
    if not company:
        cid = str(ObjectId())
        await db.companies.insert_one({"_id": ObjectId(cid), "user_id": user_id,
                                       "name": "Lumivex Photonics", "industry": "Photonics",
                                       "created_at": datetime.now(timezone.utc).isoformat()})
    else:
        cid = str(company["_id"])

    report = normalise_report_weights(lumivex_report())
    doc = {
        "_id": ObjectId(FIXED_ID),
        "user_id": user_id,
        "company_id": cid,
        "company_name": "Lumivex Photonics",
        "company_industry": "Photonics",
        "respondent_name": "A. Virtanen",
        "respondent_role": "Head of Product",
        "status": "completed",
        "chat_history": [],
        "report": report,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "completed_at": datetime.now(timezone.utc).isoformat(),
    }
    await db.assessments.replace_one({"_id": ObjectId(FIXED_ID)}, doc, upsert=True)
    print("Seeded completed assessment:", FIXED_ID)
    print("  score_current:", report["ninety_day_projection"]["score_current"],
          "-> score_projected:", report["ninety_day_projection"]["score_projected"])
    print("  bottleneck level:", report["ninety_day_projection"]["bottleneck_level_current"],
          "->", report["ninety_day_projection"]["bottleneck_level_projected"])
    client.close()


if __name__ == "__main__":
    asyncio.run(main())
