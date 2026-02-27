"""Loaders module — writes transformed data into Supabase.

Each source gets its own loader function. The loader handles upsert logic,
entity deduplication (via DB constraints), and junction row management.
"""

from otakulogs_data.loaders.jikan_anime_loader import (
    JikanAnimeLoadResult,
    load_jikan_anime_to_supabase,
)

__all__ = [
    "JikanAnimeLoadResult",
    "load_jikan_anime_to_supabase",
]
