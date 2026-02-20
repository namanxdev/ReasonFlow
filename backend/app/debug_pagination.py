import asyncio
import os
import sys
from sqlalchemy import select, func
from app.core.database import async_session_maker
from app.models.email import Email
from app.api.router import api_router  # Just to ensure models are imported

# Add backend directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

async def debug_pagination():
    async with async_session_maker() as db:
        # Get total count
        count_query = select(func.count(Email.id))
        total_result = await db.execute(count_query)
        total = total_result.scalar()
        print(f"Total emails: {total}")

        if total == 0:
            return

        # Fetch page 1 (size 10)
        page1_query = select(Email).order_by(Email.received_at.desc()).offset(0).limit(10)
        result1 = await db.execute(page1_query)
        items1 = result1.scalars().all()
        print(f"Page 1 (limit 10): {len(items1)} items")
        for e in items1:
            print(f" - {e.id} ({e.received_at})")

        # Fetch page 2 (size 10)
        page2_query = select(Email).order_by(Email.received_at.desc()).offset(10).limit(10)
        result2 = await db.execute(page2_query)
        items2 = result2.scalars().all()
        print(f"Page 2 (limit 10): {len(items2)} items")
        for e in items2:
            print(f" - {e.id} ({e.received_at})")
        
        # Check if page 2 items are different from page 1
        ids1 = {e.id for e in items1}
        ids2 = {e.id for e in items2}
        intersection = ids1.intersection(ids2)
        print(f"Intersection count: {len(intersection)}")

if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(debug_pagination())
