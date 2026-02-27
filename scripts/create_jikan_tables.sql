-- Jikan Schema — Database Tables for otakulogs-data
--
-- Run this in the Supabase SQL Editor to create the tables.
-- These tables store anime data extracted from the Jikan API (MyAnimeList wrapper).
--
-- Design decisions:
--   - UUIDs as primary keys (source-agnostic — when AniList comes, it gets its own IDs)
--   - mal_id kept as a unique reference back to MyAnimeList
--   - "type" renamed to "media_type" (SQL reserved word)
--   - "source" renamed to "source_material" (avoid confusion with our data-source concept)
--   - raw_response stores full Jikan JSON for re-processing without re-fetching
--   - Timestamps split: fetched_from_source_at (when we called Jikan) vs
--     created/updated_in_database_at (when the row hit our DB)
--   - Shared entities (genres, studios, etc.) in one table with entity_type discriminator


-- ============================================================================
-- Auto-update trigger function
-- ============================================================================
-- Automatically sets updated_in_database_at on every UPDATE.
-- Applied to tables that have this column.

create or replace function update_timestamp()
returns trigger as $$
begin
    new.updated_in_database_at = now();
    return new;
end;
$$ language plpgsql;


-- ============================================================================
-- jikan_anime — Core anime records
-- ============================================================================

create table jikan_anime (
    -- Identity
    id                      uuid primary key default gen_random_uuid(),
    mal_id                  integer not null unique,
    mal_url                 text not null,

    -- Titles
    -- JSONB array: [{"type": "Default", "title": "Cowboy Bebop"}, ...]
    titles                  jsonb not null default '[]'::jsonb,
    title_default           text,
    title_english           text,
    title_japanese          text,

    -- Classification
    media_type              text,       -- "TV", "Movie", "OVA", "ONA", "Special", "Music"
    source_material         text,       -- "Original", "Manga", "Light novel", etc.
    status                  text,       -- "Finished Airing", "Currently Airing", "Not yet aired"
    rating                  text,       -- "R - 17+", "PG-13", etc.
    season                  text,       -- "spring", "summer", "fall", "winter"
    year                    integer,

    -- Metrics
    episodes                integer,
    score                   real,
    scored_by               integer,
    rank                    integer,
    popularity              integer,
    members                 integer,
    favorites               integer,

    -- Airing dates (ISO 8601 from Jikan, stored as timestamptz)
    aired_from              timestamptz,
    aired_to                timestamptz,
    duration                text,       -- "24 min per ep" (kept as string, parsing is fragile)
    broadcast               jsonb,      -- {day, time, timezone, string}

    -- Content
    synopsis                text,
    background              text,
    approved                boolean,

    -- Rich media (stored as JSONB — complex nested structure not worth flattening)
    images                  jsonb,
    trailer                 jsonb,

    -- Raw response — full Jikan JSON for re-processing
    -- ~5KB per anime, ~150MB total for 30k entries. Cheap insurance.
    raw_response            jsonb not null,

    -- Timestamps
    fetched_from_source_at  timestamptz not null,
    created_in_database_at  timestamptz not null default now(),
    updated_in_database_at  timestamptz not null default now()
);

-- Indexes for common query patterns
create index idx_jikan_anime_media_type on jikan_anime (media_type);
create index idx_jikan_anime_status on jikan_anime (status);
create index idx_jikan_anime_season_year on jikan_anime (season, year);
create index idx_jikan_anime_score on jikan_anime (score desc nulls last);
create index idx_jikan_anime_popularity on jikan_anime (popularity);

-- Auto-update timestamp trigger
create trigger jikan_anime_update_timestamp
    before update on jikan_anime
    for each row
    execute function update_timestamp();


-- ============================================================================
-- jikan_entity — Shared entities (genres, studios, producers, etc.)
-- ============================================================================
-- Genres, themes, studios, producers, licensors, and demographics all share
-- the same shape from Jikan: {mal_id, name, type, url}. One table with an
-- entity_type discriminator avoids 6+ identical tables.

create table jikan_entity (
    id                      uuid primary key default gen_random_uuid(),
    mal_id                  integer not null,
    entity_type             text not null,  -- "genre", "theme", "studio", "producer", etc.
    name                    text not null,
    mal_url                 text not null,

    created_in_database_at  timestamptz not null default now(),
    updated_in_database_at  timestamptz not null default now(),

    -- A genre and a studio could theoretically share a mal_id,
    -- so the unique constraint includes entity_type.
    unique (entity_type, mal_id)
);

create index idx_jikan_entity_type on jikan_entity (entity_type);

-- Auto-update timestamp trigger
create trigger jikan_entity_update_timestamp
    before update on jikan_entity
    for each row
    execute function update_timestamp();


-- ============================================================================
-- jikan_anime_entity — Junction table linking anime to entities
-- ============================================================================
-- Many-to-many: an anime has many genres/studios, a genre/studio appears on
-- many anime. entity_type is denormalized here for query convenience — filter
-- "all genres for anime X" without joining back to jikan_entity.

create table jikan_anime_entity (
    anime_id                uuid not null references jikan_anime (id) on delete cascade,
    entity_id               uuid not null references jikan_entity (id) on delete cascade,
    entity_type             text not null,

    primary key (anime_id, entity_id)
);

create index idx_jikan_anime_entity_entity on jikan_anime_entity (entity_id);
create index idx_jikan_anime_entity_type on jikan_anime_entity (entity_type);
