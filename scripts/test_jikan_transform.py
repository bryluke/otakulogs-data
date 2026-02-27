"""Smoke test: fetch Cowboy Bebop from Jikan, transform it, and inspect the output.

Run: uv run python scripts/test_jikan_transform.py
"""

from datetime import UTC, datetime

import httpx

from otakulogs_data.schema import JikanAnimeResponse
from otakulogs_data.transforms import transform_jikan_anime_to_database_rows


def test_transform_cowboy_bebop() -> None:
    """Fetch Cowboy Bebop (MAL ID 1), transform it, and print the results."""
    print("--- Fetching Cowboy Bebop from Jikan API ---")

    raw_json = httpx.get("https://api.jikan.moe/v4/anime/1").json()
    response = JikanAnimeResponse.model_validate(raw_json)
    fetched_at = datetime.now(UTC)

    print(f"  Fetched: {response.data.title} (mal_id={response.data.mal_id})")
    print()

    print("--- Transforming to database rows ---")

    result = transform_jikan_anime_to_database_rows(response.data, fetched_at)

    anime_row = result.anime_row
    print("  Anime row:")
    print(f"    id:              {anime_row.id}")
    print(f"    mal_id:          {anime_row.mal_id}")
    print(f"    title_default:   {anime_row.title_default}")
    print(f"    title_english:   {anime_row.title_english}")
    print(f"    title_japanese:  {anime_row.title_japanese}")
    print(f"    media_type:      {anime_row.media_type}")
    print(f"    source_material: {anime_row.source_material}")
    print(f"    status:          {anime_row.status}")
    print(f"    episodes:        {anime_row.episodes}")
    print(f"    score:           {anime_row.score}")
    print(f"    aired_from:      {anime_row.aired_from}")
    print(f"    aired_to:        {anime_row.aired_to}")
    print(f"    season/year:     {anime_row.season} {anime_row.year}")
    print(f"    titles count:    {len(anime_row.titles)}")
    for title_entry in anime_row.titles:
        print(f"      [{title_entry['type']}] {title_entry['title']}")
    print(f"    images:          {'dict' if anime_row.images else 'None'}")
    print(f"    trailer:         {'dict' if anime_row.trailer else 'None'}")
    print(f"    broadcast:       {'dict' if anime_row.broadcast else 'None'}")
    print(f"    raw_response:    {len(str(anime_row.raw_response))} chars")
    print(f"    fetched_at:      {anime_row.fetched_from_source_at}")
    print()

    print(f"  Entity rows: {len(result.entity_rows)}")
    for entity in result.entity_rows:
        print(f"    [{entity.entity_type}] {entity.name} (mal_id={entity.mal_id}, id={entity.id})")
    print()

    print(f"  Junction rows: {len(result.anime_entity_links)}")
    for link in result.anime_entity_links:
        print(f"    anime_id={link.anime_id} -> entity_id={link.entity_id} ({link.entity_type})")
    print()


if __name__ == "__main__":
    test_transform_cowboy_bebop()
    print("Transform completed successfully against live Jikan API data!")
