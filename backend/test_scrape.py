"""Test script for App Store scraping."""

import asyncio
import httpx


async def test_scrape():
    print("=== Testing App Store Scraping ===")

    # Fetch apps from iTunes RSS
    url = "https://itunes.apple.com/us/rss/topfreeapplications/limit=10/json"
    resp = httpx.get(url, timeout=30.0)
    data = resp.json()
    apps = data.get("feed", {}).get("entry", [])
    print(f"1. Fetched {len(apps)} apps from iTunes RSS")

    if not apps:
        print("ERROR: No apps fetched!")
        return

    # Parse first app
    app_data = apps[0]
    print(f"2. Sample app: {app_data.get('im:name', {}).get('label', 'Unknown')}")

    # Save to database
    from app.database import init_db, get_db_context
    from app.models.app_store import AppStoreApp
    from sqlalchemy import select

    await init_db()

    async with get_db_context() as session:
        # Check existing
        result = await session.execute(select(AppStoreApp))
        existing = result.scalars().all()
        print(f"3. Existing apps in DB: {len(existing)}")

        if not existing:
            # Add sample app
            print("4. Adding sample app...")

            # Parse app data
            name = app_data.get("im:name", {}).get("label", "Unknown")
            developer = app_data.get("im:artist", {}).get("label", "Unknown")
            icon_url = ""
            images = app_data.get("im:image", [])
            if images:
                icon_url = images[-1].get("label", "")

            app = AppStoreApp(
                apple_app_id="test_"
                + str(app_data.get("id", {}).get("label", "0").split("/")[-1]),
                name=name,
                developer=developer,
                description=f"Test app scraped from iTunes: {name}",
                icon_url=icon_url,
                app_store_url=app_data.get("id", {}).get("label", ""),
                price=0,
                rating=4.5,
                rating_count=1000,
                is_new_release=False,
                is_rising=False,
            )
            session.add(app)
            await session.commit()
            print("5. Sample app added!")

        # Verify
        result = await session.execute(select(AppStoreApp))
        apps_in_db = result.scalars().all()
        print(f"6. Apps in DB after: {len(apps_in_db)}")

        if apps_in_db:
            for app in apps_in_db[:3]:
                print(f"   - {app.name}: {app.rating}★ ({app.rating_count} reviews)")

    print("\n=== Test Complete ===")


if __name__ == "__main__":
    asyncio.run(test_scrape())
