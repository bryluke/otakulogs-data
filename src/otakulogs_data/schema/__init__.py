"""Schema module — data models and type definitions for otakulogs-data.

Two categories of types live here:

1. **API types** (`jikan_api_types`) — Mirror the exact shape of external API
   responses. Used to validate and parse raw JSON from data sources.

2. **Database types** (`jikan_database_types`) — Represent rows in our Supabase
   tables. These are the output shape after transformation.

The transform layer (in `transforms/`) converts API types → database types.
"""

# --- Jikan API response types ---
from otakulogs_data.schema.jikan_api_types import (
    JikanAired,
    JikanAnimeData,
    JikanAnimeListResponse,
    JikanAnimeResponse,
    JikanBroadcast,
    JikanEntityReference,
    JikanImages,
    JikanPagination,
    JikanPaginationItems,
    JikanTitleEntry,
    JikanTrailer,
)

# --- Jikan database row types ---
from otakulogs_data.schema.jikan_database_types import (
    JikanAnimeDatabaseRow,
    JikanAnimeEntityLink,
    JikanEntityDatabaseRow,
)

__all__ = [
    "JikanAired",
    "JikanAnimeData",
    "JikanAnimeDatabaseRow",
    "JikanAnimeEntityLink",
    "JikanAnimeListResponse",
    "JikanAnimeResponse",
    "JikanBroadcast",
    "JikanEntityDatabaseRow",
    "JikanEntityReference",
    "JikanImages",
    "JikanPagination",
    "JikanPaginationItems",
    "JikanTitleEntry",
    "JikanTrailer",
]
