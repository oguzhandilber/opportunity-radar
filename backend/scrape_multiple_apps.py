"""Scrape multiple apps from iTunes RSS feeds and save to database."""

import asyncio
import asyncpg
import httpx
import os
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

DATABASE_CONFIG = {
    "host": os.getenv("POSTGRES_HOST", "localhost"),
    "port": int(os.getenv("POSTGRES_PORT", 5432)),
    "user": os.getenv("POSTGRES_USER", "user"),
    "password": os.getenv("POSTGRES_PASSWORD", ""),
    "database": os.getenv("POSTGRES_DB", "opportunity_radar"),
}


async def scrape_and_save_apps():
    """Fetch apps from multiple iTunes RSS feeds and save to database."""
    print("=== App Store Multi-Feed Scraper ===\n")

    feeds = [
        (
            "Top Free Apps",
            "https://itunes.apple.com/us/rss/topfreeapplications/limit=50/json",
        ),
        (
            "Top Paid Apps",
            "https://itunes.apple.com/us/rss/toppaidapplications/limit=50/json",
        ),
        (
            "New Free Apps",
            "https://itunes.apple.com/us/rss/newfreeapplications/limit=50/json",
        ),
        (
            "New Paid Apps",
            "https://itunes.apple.com/us/rss/newpaidapplications/limit=50/json",
        ),
    ]

    all_apps = []

    async with httpx.AsyncClient(timeout=30.0) as client:
        for feed_name, url in feeds:
            try:
                print(f"Fetching: {feed_name}...")
                resp = await client.get(url)
                data = resp.json()
                apps = data.get("feed", {}).get("entry", [])
                print(f"  → Found {len(apps)} apps")

                for app_data in apps:
                    name = app_data.get("im:name", {}).get("label", "Unknown")
                    developer = app_data.get("im:artist", {}).get("label", "Unknown")
                    icon_url = ""
                    images = app_data.get("im:image", [])
                    if images:
                        icon_url = images[-1].get("label", "")

                    app_id = (
                        app_data.get("id", {}).get("label", "").split("/")[-1]
                        or f"unknown_{name[:10]}"
                    )

                    price_data = app_data.get("im:price", {}).get("attributes", {})
                    price = float(price_data.get("amount", 0))

                    rating = (
                        float(
                            app_data.get("im:rating", {})
                            .get("attributes", {})
                            .get("height", 0)
                        )
                        / 2
                    )

                    all_apps.append(
                        {
                            "apple_app_id": f"id{app_id}",
                            "name": name,
                            "developer": developer,
                            "description": f"App from {feed_name}: {name}",
                            "icon_url": icon_url,
                            "app_store_url": app_data.get("id", {}).get("label", ""),
                            "price": price,
                            "rating": rating,
                            "rating_count": 0,
                            "is_new_release": "new" in feed_name.lower(),
                            "is_rising": False,
                            "feed_source": feed_name,
                        }
                    )
            except Exception as e:
                print(f"  → Error fetching {feed_name}: {e}")

    print(f"\nTotal apps collected: {len(all_apps)}")

    unique_apps = {}
    for app in all_apps:
        key = app["apple_app_id"]
        if key not in unique_apps:
            unique_apps[key] = app

    print(f"Unique apps: {len(unique_apps)}")

    # Connect to database
    print("\nConnecting to database...")
    conn = await asyncpg.connect(**DATABASE_CONFIG)

    # Get existing apps
    existing = await conn.fetch("SELECT apple_app_id FROM app_store_apps")
    existing_ids = set(row["apple_app_id"] for row in existing)
    print(f"Existing apps in DB: {len(existing_ids)}")

    saved_count = 0
    score_count = 0

    for apple_app_id, app_data in unique_apps.items():
        if apple_app_id in existing_ids:
            continue

        base_score = 50 + (app_data["rating"] * 8)
        if app_data["price"] > 0:
            base_score += 10
        if app_data["is_new_release"]:
            base_score += 5

        total_score = min(base_score, 95)

        await conn.execute(
            """
            INSERT INTO app_store_apps (
                apple_app_id, name, developer, description, icon_url,
                app_store_url, price, rating, rating_count,
                is_new_release, is_rising, scraped_at, created_at
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, NOW(), NOW())
        """,
            apple_app_id,
            app_data["name"],
            app_data["developer"],
            app_data["description"],
            app_data["icon_url"],
            app_data["app_store_url"],
            app_data["price"],
            app_data["rating"],
            app_data["rating_count"],
            app_data["is_new_release"],
            app_data["is_rising"],
        )

        await conn.execute(
            """
            INSERT INTO app_scores (
                app_id, total_opportunity_score, build_ease_score,
                revenue_potential_score, market_opportunity_score,
                rising_score, confidence_score, opportunity_summary,
                scored_at
            ) SELECT id, $1, $2, $3, $4, $5, $6, $7, NOW()
            FROM app_store_apps WHERE apple_app_id = $8
        """,
            total_score,
            min(70 + (5 if app_data["price"] > 0 else 0), 95),
            min(total_score - 5, 95),
            min(total_score, 95),
            min(50 + (10 if app_data["is_new_release"] else 0), 95),
            0.7,
            f"Scraped from {app_data['feed_source']} - {app_data['name']} by {app_data['developer']}",
            apple_app_id,
        )

        score_count += 1
        saved_count += 1
        print(f"  ✓ {app_data['name']} ({app_data['rating']}★)")

    await conn.close()

    print(f"\n=== Results ===")
    print(f"Apps saved: {saved_count}")
    print(f"Scores created: {score_count}")

    total = len(existing_ids) + saved_count
    print(f"Total apps in DB: {total}")


if __name__ == "__main__":
    asyncio.run(scrape_and_save_apps())
