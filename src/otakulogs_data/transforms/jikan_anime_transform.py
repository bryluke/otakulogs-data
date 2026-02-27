"""Transform a Jikan anime API response into database-ready rows.

One function in, three outputs out: an anime row, entity rows, and
junction rows. This is the explicit bridge between the API shape
(mirrors Jikan exactly) and the DB shape (UUIDs, renamed columns,
flattened structure).

No cross-anime entity deduplication happens here — that's the loader's
job via the DB's UNIQUE (entity_type, mal_id) constraint.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from pydantic import BaseModel

from otakulogs_data.schema.jikan_api_types import JikanAnimeData, JikanEntityReference
from otakulogs_data.schema.jikan_database_types import (
    JikanAnimeDatabaseRow,
    JikanAnimeEntityLink,
    JikanEntityDatabaseRow,
)


class JikanAnimeTransformResult(BaseModel):
    """The output of transforming one Jikan anime response.

    Named container instead of a raw tuple — self-documenting and
    easier for pyright to reason about than a 3-tuple.
    """

    anime_row: JikanAnimeDatabaseRow
    entity_rows: list[JikanEntityDatabaseRow]
    anime_entity_links: list[JikanAnimeEntityLink]


# ---------------------------------------------------------------------------
# Entity type mapping
# ---------------------------------------------------------------------------

# Maps our normalized entity type names to the attribute name on JikanAnimeData.
# We use our own type names (lowercase), NOT JikanEntityReference.type which
# contains "anime" (the parent resource type) for all of them.
ENTITY_TYPE_TO_SOURCE_ATTRIBUTE: dict[str, str] = {
    "genre": "genres",
    "explicit_genre": "explicit_genres",
    "theme": "themes",
    "demographic": "demographics",
    "producer": "producers",
    "licensor": "licensors",
    "studio": "studios",
}


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------


def _parse_iso_datetime_string_to_datetime(iso_string: str | None) -> datetime | None:
    """Parse an ISO 8601 string to a datetime, or return None for None input.

    No try/except — bad data should fail loudly so we discover it early
    rather than silently swallowing garbage dates.
    """
    if iso_string is None:
        return None
    return datetime.fromisoformat(iso_string)


def _extract_entities_from_jikan_anime(
    jikan_anime_data: JikanAnimeData,
    anime_row_id: UUID,
) -> tuple[list[JikanEntityDatabaseRow], list[JikanAnimeEntityLink]]:
    """Extract entity rows and junction rows from all 7 entity arrays.

    Each entity gets its own uuid4() ID. Deduplication across anime
    is NOT done here — the loader handles that via DB constraints.
    """
    entity_rows: list[JikanEntityDatabaseRow] = []
    junction_rows: list[JikanAnimeEntityLink] = []

    for entity_type, source_attribute in ENTITY_TYPE_TO_SOURCE_ATTRIBUTE.items():
        entity_references: list[JikanEntityReference] = getattr(
            jikan_anime_data, source_attribute
        )

        for entity_reference in entity_references:
            entity_row_id = uuid4()

            entity_rows.append(
                JikanEntityDatabaseRow(
                    id=entity_row_id,
                    mal_id=entity_reference.mal_id,
                    entity_type=entity_type,
                    name=entity_reference.name,
                    mal_url=entity_reference.url,
                )
            )

            junction_rows.append(
                JikanAnimeEntityLink(
                    anime_id=anime_row_id,
                    entity_id=entity_row_id,
                    entity_type=entity_type,
                )
            )

    return entity_rows, junction_rows


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def transform_jikan_anime_to_database_rows(
    jikan_anime_data: JikanAnimeData,
    fetched_from_source_at: datetime,
) -> JikanAnimeTransformResult:
    """Transform one Jikan anime response into database-ready rows.

    Returns:
        JikanAnimeTransformResult with:
        - anime_row: one JikanAnimeDatabaseRow
        - entity_rows: JikanEntityDatabaseRow for each entity across all 7 arrays
        - anime_entity_links: JikanAnimeEntityLink for each anime-entity pair
    """
    anime_row_id = uuid4()

    # --- Titles: merge title_synonyms into the titles JSONB array ---
    # The titles array from Jikan already includes some "Synonym" entries,
    # but title_synonyms is a separate flat list. Merge any that aren't
    # already present (checked by title text) as {"type": "Synonym", "title": "..."}.
    existing_title_texts = {entry.title for entry in jikan_anime_data.titles}

    titles_as_dicts: list[dict[str, str]] = [
        {"type": entry.type, "title": entry.title}
        for entry in jikan_anime_data.titles
    ]

    for synonym in jikan_anime_data.title_synonyms:
        if synonym not in existing_title_texts:
            titles_as_dicts.append({"type": "Synonym", "title": synonym})

    # --- Aired dates: ISO string → datetime ---
    aired_from_iso_string = jikan_anime_data.aired.from_date if jikan_anime_data.aired else None
    aired_to_iso_string = jikan_anime_data.aired.to if jikan_anime_data.aired else None

    aired_from_datetime = _parse_iso_datetime_string_to_datetime(aired_from_iso_string)
    aired_to_datetime = _parse_iso_datetime_string_to_datetime(aired_to_iso_string)

    # --- Nested models → plain dicts for JSONB storage ---
    images_as_dict = jikan_anime_data.images.model_dump() if jikan_anime_data.images else None
    trailer_as_dict = jikan_anime_data.trailer.model_dump() if jikan_anime_data.trailer else None
    broadcast_as_dict = (
        jikan_anime_data.broadcast.model_dump() if jikan_anime_data.broadcast else None
    )

    # --- Raw response: full model dump for re-processing later ---
    raw_response_dict = jikan_anime_data.model_dump()

    # --- Build the anime row ---
    anime_row = JikanAnimeDatabaseRow(
        id=anime_row_id,
        mal_id=jikan_anime_data.mal_id,
        mal_url=jikan_anime_data.url,
        titles=titles_as_dicts,
        title_default=jikan_anime_data.title,
        title_english=jikan_anime_data.title_english,
        title_japanese=jikan_anime_data.title_japanese,
        media_type=jikan_anime_data.type,
        source_material=jikan_anime_data.source,
        status=jikan_anime_data.status,
        rating=jikan_anime_data.rating,
        season=jikan_anime_data.season,
        year=jikan_anime_data.year,
        episodes=jikan_anime_data.episodes,
        score=jikan_anime_data.score,
        scored_by=jikan_anime_data.scored_by,
        rank=jikan_anime_data.rank,
        popularity=jikan_anime_data.popularity,
        members=jikan_anime_data.members,
        favorites=jikan_anime_data.favorites,
        aired_from=aired_from_datetime,
        aired_to=aired_to_datetime,
        duration=jikan_anime_data.duration,
        broadcast=broadcast_as_dict,
        synopsis=jikan_anime_data.synopsis,
        background=jikan_anime_data.background,
        approved=jikan_anime_data.approved,
        images=images_as_dict,
        trailer=trailer_as_dict,
        raw_response=raw_response_dict,
        fetched_from_source_at=fetched_from_source_at,
        # DB triggers handle these — leave as None
        created_in_database_at=None,
        updated_in_database_at=None,
    )

    # --- Extract entities and junction rows ---
    entity_rows, anime_entity_links = _extract_entities_from_jikan_anime(
        jikan_anime_data, anime_row_id
    )

    return JikanAnimeTransformResult(
        anime_row=anime_row,
        entity_rows=entity_rows,
        anime_entity_links=anime_entity_links,
    )
