"""Tests for the Jikan anime transform layer.

All fixtures are hardcoded — no file loading, no live API calls.
Each test verifies a specific aspect of the API-to-DB transformation.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from otakulogs_data.schema.jikan_api_types import (
    JikanAired,
    JikanAnimeData,
    JikanBroadcast,
    JikanEntityReference,
    JikanImages,
    JikanImageUrls,
    JikanTitleEntry,
    JikanTrailer,
)
from otakulogs_data.transforms.jikan_anime_transform import (
    transform_jikan_anime_to_database_rows,
)

# ---------------------------------------------------------------------------
# Shared fixture builder
# ---------------------------------------------------------------------------

SAMPLE_FETCHED_AT = datetime(2026, 2, 27, 12, 0, 0)


def _build_sample_jikan_anime_data() -> JikanAnimeData:
    """Build a realistic JikanAnimeData with all fields populated."""
    return JikanAnimeData(
        mal_id=1,
        url="https://myanimelist.net/anime/1/Cowboy_Bebop",
        images=JikanImages(
            jpg=JikanImageUrls(
                image_url="https://cdn.myanimelist.net/images/anime/4/19644.jpg",
                small_image_url="https://cdn.myanimelist.net/images/anime/4/19644t.jpg",
                large_image_url="https://cdn.myanimelist.net/images/anime/4/19644l.jpg",
            ),
        ),
        trailer=JikanTrailer(
            youtube_id="qig4KOK2R2g",
            url="https://www.youtube.com/watch?v=qig4KOK2R2g",
            embed_url="https://www.youtube.com/embed/qig4KOK2R2g",
        ),
        approved=True,
        titles=[
            JikanTitleEntry(type="Default", title="Cowboy Bebop"),
            JikanTitleEntry(type="Synonym", title="COWBOY BEBOP"),
            JikanTitleEntry(
                type="Japanese", title="\u30ab\u30a6\u30dc\u30fc\u30a4\u30d3\u30d0\u30c3\u30d7"
            ),
            JikanTitleEntry(type="English", title="Cowboy Bebop"),
        ],
        title="Cowboy Bebop",
        title_english="Cowboy Bebop",
        title_japanese="\u30ab\u30a6\u30dc\u30fc\u30a4\u30d3\u30d0\u30c3\u30d7",
        title_synonyms=["COWBOY BEBOP", "CB"],
        type="TV",
        source="Original",
        status="Finished Airing",
        rating="R - 17+ (violence & profanity)",
        episodes=26,
        score=8.75,
        scored_by=900000,
        rank=28,
        popularity=43,
        members=1800000,
        favorites=80000,
        airing=False,
        aired=JikanAired(
            from_date="1998-04-03T00:00:00+00:00",
            to="1999-04-24T00:00:00+00:00",
            string="Apr 3, 1998 to Apr 24, 1999",
        ),
        duration="24 min per ep",
        season="spring",
        year=1998,
        broadcast=JikanBroadcast(
            day="Saturdays",
            time="01:00",
            timezone="Asia/Tokyo",
            string="Saturdays at 01:00 (JST)",
        ),
        synopsis="A bounty hunter crew in space.",
        background="Cowboy Bebop is widely regarded as a masterpiece.",
        genres=[
            JikanEntityReference(mal_id=1, type="anime", name="Action", url="https://myanimelist.net/anime/genre/1/Action"),
            JikanEntityReference(mal_id=24, type="anime", name="Sci-Fi", url="https://myanimelist.net/anime/genre/24/Sci-Fi"),
        ],
        explicit_genres=[],
        themes=[
            JikanEntityReference(mal_id=50, type="anime", name="Adult Cast", url="https://myanimelist.net/anime/genre/50/Adult_Cast"),
            JikanEntityReference(mal_id=29, type="anime", name="Space", url="https://myanimelist.net/anime/genre/29/Space"),
        ],
        demographics=[],
        producers=[
            JikanEntityReference(mal_id=23, type="anime", name="Bandai Visual", url="https://myanimelist.net/anime/producer/23/Bandai_Visual"),
        ],
        licensors=[
            JikanEntityReference(mal_id=102, type="anime", name="Funimation", url="https://myanimelist.net/anime/producer/102/Funimation"),
        ],
        studios=[
            JikanEntityReference(mal_id=14, type="anime", name="Sunrise", url="https://myanimelist.net/anime/producer/14/Sunrise"),
        ],
    )


def _build_minimal_jikan_anime_data() -> JikanAnimeData:
    """Build JikanAnimeData with only required fields — everything else null/empty."""
    return JikanAnimeData(
        mal_id=99999,
        url="https://myanimelist.net/anime/99999/Test",
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestAnimeRowDirectCopyFields:
    """Fields that pass through without renaming or transformation."""

    def test_episodes_score_status_pass_through(self) -> None:
        anime_data = _build_sample_jikan_anime_data()
        result = transform_jikan_anime_to_database_rows(anime_data, SAMPLE_FETCHED_AT)

        assert result.anime_row.episodes == 26
        assert result.anime_row.score == 8.75
        assert result.anime_row.status == "Finished Airing"
        assert result.anime_row.scored_by == 900000
        assert result.anime_row.rank == 28
        assert result.anime_row.popularity == 43
        assert result.anime_row.members == 1800000
        assert result.anime_row.favorites == 80000
        assert result.anime_row.season == "spring"
        assert result.anime_row.year == 1998
        assert result.anime_row.duration == "24 min per ep"
        assert result.anime_row.rating == "R - 17+ (violence & profanity)"
        assert result.anime_row.synopsis == "A bounty hunter crew in space."
        assert result.anime_row.background == "Cowboy Bebop is widely regarded as a masterpiece."
        assert result.anime_row.approved is True


class TestAnimeRowRenamedFields:
    """Fields that get renamed from Jikan conventions to our DB conventions."""

    def test_url_becomes_mal_url(self) -> None:
        anime_data = _build_sample_jikan_anime_data()
        result = transform_jikan_anime_to_database_rows(anime_data, SAMPLE_FETCHED_AT)
        assert result.anime_row.mal_url == "https://myanimelist.net/anime/1/Cowboy_Bebop"

    def test_title_becomes_title_default(self) -> None:
        anime_data = _build_sample_jikan_anime_data()
        result = transform_jikan_anime_to_database_rows(anime_data, SAMPLE_FETCHED_AT)
        assert result.anime_row.title_default == "Cowboy Bebop"

    def test_type_becomes_media_type(self) -> None:
        anime_data = _build_sample_jikan_anime_data()
        result = transform_jikan_anime_to_database_rows(anime_data, SAMPLE_FETCHED_AT)
        assert result.anime_row.media_type == "TV"

    def test_source_becomes_source_material(self) -> None:
        anime_data = _build_sample_jikan_anime_data()
        result = transform_jikan_anime_to_database_rows(anime_data, SAMPLE_FETCHED_AT)
        assert result.anime_row.source_material == "Original"


class TestAiredDatesParsedToDatetime:
    """ISO strings from the API become datetime objects in the DB row."""

    def test_aired_from_parsed(self) -> None:
        anime_data = _build_sample_jikan_anime_data()
        result = transform_jikan_anime_to_database_rows(anime_data, SAMPLE_FETCHED_AT)
        assert isinstance(result.anime_row.aired_from, datetime)
        assert result.anime_row.aired_from.year == 1998
        assert result.anime_row.aired_from.month == 4
        assert result.anime_row.aired_from.day == 3

    def test_aired_to_parsed(self) -> None:
        anime_data = _build_sample_jikan_anime_data()
        result = transform_jikan_anime_to_database_rows(anime_data, SAMPLE_FETCHED_AT)
        assert isinstance(result.anime_row.aired_to, datetime)
        assert result.anime_row.aired_to.year == 1999

    def test_none_stays_none(self) -> None:
        anime_data = _build_minimal_jikan_anime_data()
        result = transform_jikan_anime_to_database_rows(anime_data, SAMPLE_FETCHED_AT)
        assert result.anime_row.aired_from is None
        assert result.anime_row.aired_to is None


class TestNestedModelsSerializedToDicts:
    """Pydantic models (images, trailer, broadcast) become plain dicts for JSONB."""

    def test_images_is_dict(self) -> None:
        anime_data = _build_sample_jikan_anime_data()
        result = transform_jikan_anime_to_database_rows(anime_data, SAMPLE_FETCHED_AT)
        assert isinstance(result.anime_row.images, dict)
        assert "jpg" in result.anime_row.images

    def test_trailer_is_dict(self) -> None:
        anime_data = _build_sample_jikan_anime_data()
        result = transform_jikan_anime_to_database_rows(anime_data, SAMPLE_FETCHED_AT)
        assert isinstance(result.anime_row.trailer, dict)
        assert result.anime_row.trailer["youtube_id"] == "qig4KOK2R2g"

    def test_broadcast_is_dict(self) -> None:
        anime_data = _build_sample_jikan_anime_data()
        result = transform_jikan_anime_to_database_rows(anime_data, SAMPLE_FETCHED_AT)
        assert isinstance(result.anime_row.broadcast, dict)
        assert result.anime_row.broadcast["day"] == "Saturdays"

    def test_none_models_stay_none(self) -> None:
        anime_data = _build_minimal_jikan_anime_data()
        result = transform_jikan_anime_to_database_rows(anime_data, SAMPLE_FETCHED_AT)
        assert result.anime_row.images is None
        assert result.anime_row.trailer is None
        assert result.anime_row.broadcast is None


class TestTitlesIncludeMergedSynonyms:
    """title_synonyms entries get merged into the titles JSONB array."""

    def test_synonyms_merged_without_duplicates(self) -> None:
        anime_data = _build_sample_jikan_anime_data()
        result = transform_jikan_anime_to_database_rows(anime_data, SAMPLE_FETCHED_AT)

        title_texts = [t["title"] for t in result.anime_row.titles]

        # "COWBOY BEBOP" is already in the titles array as a Synonym entry,
        # so it should appear exactly once (not duplicated from title_synonyms)
        assert title_texts.count("COWBOY BEBOP") == 1

        # "CB" is only in title_synonyms, so it should be merged in
        assert "CB" in title_texts

    def test_merged_synonyms_have_synonym_type(self) -> None:
        anime_data = _build_sample_jikan_anime_data()
        result = transform_jikan_anime_to_database_rows(anime_data, SAMPLE_FETCHED_AT)

        cb_entries = [t for t in result.anime_row.titles if t["title"] == "CB"]
        assert len(cb_entries) == 1
        assert cb_entries[0]["type"] == "Synonym"

    def test_titles_are_dicts_not_models(self) -> None:
        anime_data = _build_sample_jikan_anime_data()
        result = transform_jikan_anime_to_database_rows(anime_data, SAMPLE_FETCHED_AT)

        for title_entry in result.anime_row.titles:
            assert isinstance(title_entry, dict)
            assert "type" in title_entry
            assert "title" in title_entry


class TestEntityExtractionAllTypes:
    """All 7 entity arrays get extracted into entity rows with correct types."""

    def test_correct_total_entity_count(self) -> None:
        anime_data = _build_sample_jikan_anime_data()
        result = transform_jikan_anime_to_database_rows(anime_data, SAMPLE_FETCHED_AT)

        # 2 genres + 0 explicit_genres + 2 themes + 0 demographics
        # + 1 producer + 1 licensor + 1 studio = 7 total
        assert len(result.entity_rows) == 7

    def test_entity_types_are_our_normalized_names(self) -> None:
        anime_data = _build_sample_jikan_anime_data()
        result = transform_jikan_anime_to_database_rows(anime_data, SAMPLE_FETCHED_AT)

        entity_types = {e.entity_type for e in result.entity_rows}
        assert entity_types == {"genre", "theme", "producer", "licensor", "studio"}

    def test_entity_names_preserved(self) -> None:
        anime_data = _build_sample_jikan_anime_data()
        result = transform_jikan_anime_to_database_rows(anime_data, SAMPLE_FETCHED_AT)

        entity_names = {e.name for e in result.entity_rows}
        assert "Action" in entity_names
        assert "Sci-Fi" in entity_names
        assert "Sunrise" in entity_names
        assert "Funimation" in entity_names
        assert "Bandai Visual" in entity_names

    def test_entity_mal_ids_preserved(self) -> None:
        anime_data = _build_sample_jikan_anime_data()
        result = transform_jikan_anime_to_database_rows(anime_data, SAMPLE_FETCHED_AT)

        entity_mal_ids = {e.mal_id for e in result.entity_rows}
        assert 1 in entity_mal_ids  # Action genre
        assert 14 in entity_mal_ids  # Sunrise studio


class TestJunctionRowsLinkAnimeToEntities:
    """Junction rows correctly link anime_id to entity_id."""

    def test_junction_count_matches_entity_count(self) -> None:
        anime_data = _build_sample_jikan_anime_data()
        result = transform_jikan_anime_to_database_rows(anime_data, SAMPLE_FETCHED_AT)
        assert len(result.anime_entity_links) == len(result.entity_rows)

    def test_all_junction_rows_reference_anime_id(self) -> None:
        anime_data = _build_sample_jikan_anime_data()
        result = transform_jikan_anime_to_database_rows(anime_data, SAMPLE_FETCHED_AT)

        for link in result.anime_entity_links:
            assert link.anime_id == result.anime_row.id

    def test_junction_entity_ids_match_entity_rows(self) -> None:
        anime_data = _build_sample_jikan_anime_data()
        result = transform_jikan_anime_to_database_rows(anime_data, SAMPLE_FETCHED_AT)

        entity_ids_from_rows = {e.id for e in result.entity_rows}
        entity_ids_from_links = {link.entity_id for link in result.anime_entity_links}
        assert entity_ids_from_links == entity_ids_from_rows


class TestRawResponseIsFullModelDump:
    """raw_response should contain the complete serialized input."""

    def test_raw_response_has_mal_id(self) -> None:
        anime_data = _build_sample_jikan_anime_data()
        result = transform_jikan_anime_to_database_rows(anime_data, SAMPLE_FETCHED_AT)

        assert result.anime_row.raw_response["mal_id"] == 1
        assert result.anime_row.raw_response["url"] == "https://myanimelist.net/anime/1/Cowboy_Bebop"

    def test_raw_response_has_nested_structures(self) -> None:
        anime_data = _build_sample_jikan_anime_data()
        result = transform_jikan_anime_to_database_rows(anime_data, SAMPLE_FETCHED_AT)

        assert "genres" in result.anime_row.raw_response
        assert "aired" in result.anime_row.raw_response
        assert isinstance(result.anime_row.raw_response["genres"], list)


class TestDbTimestampsAreNone:
    """created/updated_in_database_at are left for DB triggers."""

    def test_created_in_database_at_is_none(self) -> None:
        anime_data = _build_sample_jikan_anime_data()
        result = transform_jikan_anime_to_database_rows(anime_data, SAMPLE_FETCHED_AT)
        assert result.anime_row.created_in_database_at is None

    def test_updated_in_database_at_is_none(self) -> None:
        anime_data = _build_sample_jikan_anime_data()
        result = transform_jikan_anime_to_database_rows(anime_data, SAMPLE_FETCHED_AT)
        assert result.anime_row.updated_in_database_at is None

    def test_fetched_from_source_at_is_set(self) -> None:
        anime_data = _build_sample_jikan_anime_data()
        result = transform_jikan_anime_to_database_rows(anime_data, SAMPLE_FETCHED_AT)
        assert result.anime_row.fetched_from_source_at == SAMPLE_FETCHED_AT

    def test_entity_timestamps_are_none(self) -> None:
        anime_data = _build_sample_jikan_anime_data()
        result = transform_jikan_anime_to_database_rows(anime_data, SAMPLE_FETCHED_AT)

        for entity in result.entity_rows:
            assert entity.created_in_database_at is None
            assert entity.updated_in_database_at is None


class TestUuidGeneration:
    """Anime row and entity rows get valid UUIDs."""

    def test_anime_row_has_uuid(self) -> None:
        anime_data = _build_sample_jikan_anime_data()
        result = transform_jikan_anime_to_database_rows(anime_data, SAMPLE_FETCHED_AT)
        assert isinstance(result.anime_row.id, UUID)

    def test_entity_rows_have_uuids(self) -> None:
        anime_data = _build_sample_jikan_anime_data()
        result = transform_jikan_anime_to_database_rows(anime_data, SAMPLE_FETCHED_AT)

        for entity in result.entity_rows:
            assert isinstance(entity.id, UUID)

    def test_all_uuids_are_unique(self) -> None:
        anime_data = _build_sample_jikan_anime_data()
        result = transform_jikan_anime_to_database_rows(anime_data, SAMPLE_FETCHED_AT)

        all_ids = [result.anime_row.id] + [e.id for e in result.entity_rows]
        assert len(all_ids) == len(set(all_ids))


class TestMinimalAnimeWithAllNulls:
    """Anime with only required fields transforms without errors."""

    def test_minimal_anime_transforms_cleanly(self) -> None:
        anime_data = _build_minimal_jikan_anime_data()
        result = transform_jikan_anime_to_database_rows(anime_data, SAMPLE_FETCHED_AT)

        assert result.anime_row.mal_id == 99999
        assert result.anime_row.mal_url == "https://myanimelist.net/anime/99999/Test"
        assert result.anime_row.title_default is None
        assert result.anime_row.title_english is None
        assert result.anime_row.media_type is None
        assert result.anime_row.episodes is None
        assert result.anime_row.score is None

    def test_minimal_anime_has_empty_entities(self) -> None:
        anime_data = _build_minimal_jikan_anime_data()
        result = transform_jikan_anime_to_database_rows(anime_data, SAMPLE_FETCHED_AT)

        assert len(result.entity_rows) == 0
        assert len(result.anime_entity_links) == 0

    def test_minimal_anime_has_empty_titles(self) -> None:
        anime_data = _build_minimal_jikan_anime_data()
        result = transform_jikan_anime_to_database_rows(anime_data, SAMPLE_FETCHED_AT)

        assert result.anime_row.titles == []
