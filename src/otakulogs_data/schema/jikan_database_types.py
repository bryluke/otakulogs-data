"""Pydantic models representing rows in our Jikan database tables.

These are the *output* shape — what we store in Supabase after transforming
Jikan API responses. They differ from the API types in several ways:

- Our own UUID primary keys (source-agnostic, ready for multi-source)
- Renamed columns: `type` → `media_type`, `source` → `source_material`
- Flattened structure (no nesting — one model per table row)
- Timestamps split: `fetched_from_source_at` vs `created/updated_in_database_at`
- Raw JSON preserved in `raw_response` for re-processing

The transform layer (not yet built) converts API types → these DB types.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class JikanAnimeDatabaseRow(BaseModel):
    """A row in the `jikan_anime` table.

    Stores one anime's worth of data as extracted from Jikan.
    `mal_id` is kept as a unique reference back to MyAnimeList,
    but our `id` (UUID) is the primary key — when we later add
    AniList or other sources, each gets its own IDs.
    """

    model_config = ConfigDict(from_attributes=True)

    # --- Identity ---
    id: UUID
    mal_id: int
    mal_url: str

    # --- Titles ---
    # Stored as JSONB array: [{"type": "Default", "title": "Cowboy Bebop"}, ...]
    titles: list[dict[str, str]]
    title_default: str | None = None
    title_english: str | None = None
    title_japanese: str | None = None

    # --- Classification ---
    # "type" renamed to "media_type" — avoids SQL reserved word
    # "source" renamed to "source_material" — avoids confusion with our
    # data-source concept (Jikan, AniList, etc.)
    media_type: str | None = None
    source_material: str | None = None
    status: str | None = None
    rating: str | None = None
    season: str | None = None
    year: int | None = None

    # --- Metrics ---
    episodes: int | None = None
    score: float | None = None
    scored_by: int | None = None
    rank: int | None = None
    popularity: int | None = None
    members: int | None = None
    favorites: int | None = None

    # --- Airing ---
    # ISO 8601 timestamps (Jikan provides these as strings, we parse to datetime)
    aired_from: datetime | None = None
    aired_to: datetime | None = None
    duration: str | None = None
    broadcast: dict[str, Any] | None = None

    # --- Content ---
    synopsis: str | None = None
    background: str | None = None
    approved: bool | None = None

    # --- Rich media (stored as JSONB) ---
    images: dict[str, Any] | None = None
    trailer: dict[str, Any] | None = None

    # --- Raw response ---
    # Full Jikan response preserved as JSONB. Cheap insurance (~5KB per anime,
    # ~150MB total for 30k entries). Lets us re-process without re-fetching
    # if we discover bugs or want to extract additional fields later.
    raw_response: dict[str, Any]

    # --- Timestamps ---
    # When we called the Jikan API (set by our extraction code)
    fetched_from_source_at: datetime
    # When this row was inserted/updated (set by database triggers)
    created_in_database_at: datetime | None = None
    updated_in_database_at: datetime | None = None


class JikanEntityDatabaseRow(BaseModel):
    """A row in the `jikan_entity` table.

    Genres, themes, studios, producers, licensors, and demographics
    all share the same shape from Jikan: `{mal_id, name, type, url}`.
    Rather than creating 6 identical tables, we use one table with an
    `entity_type` discriminator column.

    Entity types: genre, explicit_genre, theme, demographic, producer,
    licensor, studio.
    """

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    mal_id: int
    entity_type: str
    name: str
    mal_url: str

    created_in_database_at: datetime | None = None
    updated_in_database_at: datetime | None = None


class JikanAnimeEntityLink(BaseModel):
    """A row in the `jikan_anime_entity` junction table.

    Links an anime to an entity (genre, studio, etc.) with the
    `entity_type` denormalized for query convenience — so you can
    filter "all genres for anime X" without joining back to jikan_entity.
    """

    model_config = ConfigDict(from_attributes=True)

    anime_id: UUID
    entity_id: UUID
    entity_type: str
