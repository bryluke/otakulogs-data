"""Quick smoke test: fetch Cowboy Bebop from Jikan and parse through our models.

Run: uv run python scripts/test_jikan_schema.py
"""

import httpx

from otakulogs_data.schema import (
    JikanAnimeListResponse,
    JikanAnimeResponse,
)


def test_single_anime_response() -> None:
    """Fetch a single anime (Cowboy Bebop, mal_id=1) and validate the response."""
    print("--- Single anime response (Cowboy Bebop) ---")

    raw_json = httpx.get("https://api.jikan.moe/v4/anime/1").json()
    response = JikanAnimeResponse.model_validate(raw_json)

    anime = response.data
    print(f"  mal_id:    {anime.mal_id}")
    print(f"  title:     {anime.title}")
    print(f"  type:      {anime.type}")
    print(f"  episodes:  {anime.episodes}")
    print(f"  score:     {anime.score}")
    print(f"  status:    {anime.status}")
    print(f"  titles:    {len(anime.titles)} variants")
    for title_entry in anime.titles:
        print(f"    [{title_entry.type}] {title_entry.title}")
    print(f"  genres:    {[g.name for g in anime.genres]}")
    print(f"  studios:   {[s.name for s in anime.studios]}")
    print(f"  aired:     {anime.aired}")
    print()


def test_paginated_list_response() -> None:
    """Fetch a page of anime and validate the paginated response."""
    print("--- Paginated list response (page 1, 3 items) ---")

    raw_json = httpx.get(
        "https://api.jikan.moe/v4/anime",
        params={"order_by": "mal_id", "sort": "asc", "page": 1, "limit": 3},
    ).json()
    response = JikanAnimeListResponse.model_validate(raw_json)

    print(f"  total anime:      {response.pagination.items and response.pagination.items.total}")
    print(f"  last page:        {response.pagination.last_visible_page}")
    print(f"  has_next_page:    {response.pagination.has_next_page}")
    print(f"  items on page:    {len(response.data)}")
    for anime in response.data:
        print(f"    [{anime.mal_id}] {anime.title} ({anime.type})")
    print()


if __name__ == "__main__":
    test_single_anime_response()
    test_paginated_list_response()
    print("All models validated successfully against live Jikan API data!")
