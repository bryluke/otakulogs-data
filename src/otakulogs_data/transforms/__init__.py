"""Transforms module — converts source API data into database-ready rows.

Each source gets its own transform function. The transform step is explicit:
API types (exact mirror of source) → DB types (our schema with UUIDs,
renamed columns, flattened structure).
"""

from otakulogs_data.transforms.jikan_anime_transform import (
    JikanAnimeTransformResult,
    transform_jikan_anime_to_database_rows,
)

__all__ = [
    "JikanAnimeTransformResult",
    "transform_jikan_anime_to_database_rows",
]
