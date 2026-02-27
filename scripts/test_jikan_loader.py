"""Smoke test: full pipeline from Jikan API to Supabase.

Fetches Cowboy Bebop → validates → transforms → loads → queries back to verify.
Safe to run multiple times — upserts update existing rows, no duplicates.

Run: uv run python scripts/test_jikan_loader.py
"""

import os
from datetime import UTC, datetime
from pathlib import Path

import httpx
from dotenv import load_dotenv
from supabase import create_client

from otakulogs_data.loaders import load_jikan_anime_to_supabase
from otakulogs_data.schema import JikanAnimeResponse
from otakulogs_data.transforms import transform_jikan_anime_to_database_rows

# Load credentials from .context/.env (gitignored)
load_dotenv(Path(__file__).resolve().parent.parent / ".context" / ".env")

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_SERVICE_KEY = os.environ["SUPABASE_SERVICE_KEY"]


def test_full_pipeline_cowboy_bebop() -> None:
    """Fetch, validate, transform, load, and verify Cowboy Bebop."""

    # --- Step 1: Fetch from Jikan API ---
    print("--- Step 1: Fetching Cowboy Bebop from Jikan API ---")

    raw_json = httpx.get("https://api.jikan.moe/v4/anime/1").json()
    response = JikanAnimeResponse.model_validate(raw_json)
    fetched_at = datetime.now(UTC)

    print(f"  Fetched: {response.data.title} (mal_id={response.data.mal_id})")
    print()

    # --- Step 2: Transform ---
    print("--- Step 2: Transforming to database rows ---")

    transform_result = transform_jikan_anime_to_database_rows(response.data, fetched_at)

    print(f"  Anime: {transform_result.anime_row.title_default}")
    print(f"  Entities: {len(transform_result.entity_rows)}")
    print(f"  Junctions: {len(transform_result.anime_entity_links)}")
    print()

    # --- Step 3: Load into Supabase ---
    print("--- Step 3: Loading into Supabase ---")

    supabase_client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
    load_result = load_jikan_anime_to_supabase(transform_result, supabase_client)

    print(f"  Anime ID (DB): {load_result.anime_id}")
    print(f"  Entities upserted: {load_result.entity_count}")
    print(f"  Junctions inserted: {load_result.junction_count}")
    print()

    # --- Step 4: Verify by querying back ---
    print("--- Step 4: Verifying data in Supabase ---")

    anime_check = (
        supabase_client.table("jikan_anime")
        .select("id, mal_id, title_default, media_type, score, episodes")
        .eq("mal_id", 1)
        .execute()
    )

    if anime_check.data:
        row = anime_check.data[0]
        print(f"  jikan_anime row:")
        print(f"    id:            {row['id']}")  # type: ignore[index]
        print(f"    mal_id:        {row['mal_id']}")  # type: ignore[index]
        print(f"    title_default: {row['title_default']}")  # type: ignore[index]
        print(f"    media_type:    {row['media_type']}")  # type: ignore[index]
        print(f"    score:         {row['score']}")  # type: ignore[index]
        print(f"    episodes:      {row['episodes']}")  # type: ignore[index]
    else:
        print("  ERROR: No anime row found for mal_id=1!")

    entity_check = (
        supabase_client.table("jikan_entity")
        .select("id, entity_type, name, mal_id")
        .execute()
    )
    print(f"\n  jikan_entity rows: {len(entity_check.data)}")
    for entity in entity_check.data:
        print(f"    [{entity['entity_type']}] {entity['name']} (mal_id={entity['mal_id']})")  # type: ignore[index]

    junction_check = (
        supabase_client.table("jikan_anime_entity")
        .select("anime_id, entity_id, entity_type")
        .eq("anime_id", load_result.anime_id)
        .execute()
    )
    print(f"\n  jikan_anime_entity rows for this anime: {len(junction_check.data)}")
    for link in junction_check.data:
        print(f"    {link['entity_type']}: entity_id={link['entity_id']}")  # type: ignore[index]

    print()


if __name__ == "__main__":
    test_full_pipeline_cowboy_bebop()
    print("Full pipeline completed successfully!")
