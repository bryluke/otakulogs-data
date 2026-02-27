"""Load transformed Jikan anime data into Supabase.

Takes the output of transform_jikan_anime_to_database_rows() and upserts it
into three tables: jikan_anime, jikan_entity, jikan_anime_entity.

The key challenge is entity deduplication. The transform generates fresh UUIDs
for every entity, but entities are shared across anime — "Action" (mal_id=1)
appears on thousands of anime. We solve this by NOT sending IDs to the DB:
Postgres generates UUIDs via gen_random_uuid() on insert, and existing rows
keep their IDs on conflict. The upsert response returns actual DB UUIDs,
which we use for junction rows.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel
from supabase import Client

from otakulogs_data.transforms.jikan_anime_transform import JikanAnimeTransformResult


class JikanAnimeLoadResult(BaseModel):
    """Result of loading one anime into Supabase.

    Consistent with JikanAnimeTransformResult — named container for logging
    and pipeline orchestration.
    """

    anime_id: str
    entity_count: int
    junction_count: int


# Fields managed by the database, not by us. Excluded from all upserts
# so Postgres defaults and triggers handle them.
_DB_MANAGED_FIELDS = {"id", "created_in_database_at", "updated_in_database_at"}


def _rows_from_response(data: list[Any]) -> list[dict[str, Any]]:
    """Cast Supabase response data to a list of row dicts.

    PostgREST always returns rows as JSON objects, but the supabase-py
    type stubs declare response.data as list[JSON] (a broad union).
    This helper narrows the type for pyright strict mode.
    """
    result: list[dict[str, Any]] = data
    return result


def load_jikan_anime_to_supabase(
    transform_result: JikanAnimeTransformResult,
    supabase_client: Client,
) -> JikanAnimeLoadResult:
    """Upsert one anime's transform output into Supabase.

    Three-step process:
    1. Upsert anime row (on_conflict=mal_id)
    2. Upsert entity rows (on_conflict=entity_type,mal_id) — returns actual DB UUIDs
    3. Delete-then-insert junction rows — cleanly handles removed associations

    Args:
        transform_result: Output from transform_jikan_anime_to_database_rows().
        supabase_client: An authenticated Supabase client (caller handles credentials).

    Returns:
        JikanAnimeLoadResult with the actual DB UUID and row counts.
    """

    # --- Step 1: Upsert the anime row ---
    # mode="json" serializes UUIDs to strings and datetimes to ISO strings,
    # which is what PostgREST expects over HTTP.
    anime_data = transform_result.anime_row.model_dump(
        mode="json",
        exclude=_DB_MANAGED_FIELDS,
    )

    anime_response = (
        supabase_client.table("jikan_anime")
        .upsert(anime_data, on_conflict="mal_id")
        .execute()
    )

    anime_rows = _rows_from_response(anime_response.data)
    actual_anime_id: str = anime_rows[0]["id"]

    # --- Step 2: Upsert entity rows ---
    # Each entity might already exist from a previous anime load. The DB's
    # UNIQUE (entity_type, mal_id) constraint handles dedup — on conflict,
    # we update the name and URL (entities can get renamed on MAL).
    entity_count = 0

    # Lookup table: (entity_type, mal_id) → actual DB UUID string.
    # Needed in step 3 to wire junction rows to real entity IDs.
    entity_id_lookup: dict[tuple[str, int], str] = {}

    if transform_result.entity_rows:
        entity_dicts = [
            entity_row.model_dump(mode="json", exclude=_DB_MANAGED_FIELDS)
            for entity_row in transform_result.entity_rows
        ]

        entity_response = (
            supabase_client.table("jikan_entity")
            .upsert(entity_dicts, on_conflict="entity_type,mal_id")
            .execute()
        )

        entity_rows = _rows_from_response(entity_response.data)
        entity_count = len(entity_rows)

        entity_id_lookup = {
            (row["entity_type"], row["mal_id"]): row["id"]
            for row in entity_rows
        }

    # --- Step 3: Replace junction rows ---
    # Delete-then-insert instead of upsert. This cleanly handles the case
    # where an anime loses a genre or studio on re-fetch — stale links
    # get removed. Cascading deletes on the FK would also work, but
    # explicit delete is clearer about intent.
    supabase_client.table("jikan_anime_entity").delete().eq(
        "anime_id", actual_anime_id
    ).execute()

    junction_count = 0

    if entity_id_lookup:
        junction_dicts = [
            {
                "anime_id": actual_anime_id,
                "entity_id": entity_id_lookup[(entity_row.entity_type, entity_row.mal_id)],
                "entity_type": entity_row.entity_type,
            }
            for entity_row in transform_result.entity_rows
        ]

        supabase_client.table("jikan_anime_entity").insert(junction_dicts).execute()
        junction_count = len(junction_dicts)

    return JikanAnimeLoadResult(
        anime_id=actual_anime_id,
        entity_count=entity_count,
        junction_count=junction_count,
    )
