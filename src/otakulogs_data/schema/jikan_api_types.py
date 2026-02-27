"""Pydantic models that mirror Jikan API response shapes exactly.

These models validate and parse raw JSON from the Jikan v4 API.
They intentionally match the API's naming and nesting — no renaming,
no reshaping. That transformation happens in a separate step when
converting to database types.

Reference: https://docs.api.jikan.moe/
Explored in: .context/exploration-jikan.md
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict

# ---------------------------------------------------------------------------
# Shared / nested structures
# ---------------------------------------------------------------------------


class JikanImageUrls(BaseModel):
    """A set of image URLs at different sizes (jpg or webp)."""

    model_config = ConfigDict(extra="allow")

    image_url: str | None = None
    small_image_url: str | None = None
    large_image_url: str | None = None


class JikanImages(BaseModel):
    """Container for jpg and webp image variants."""

    jpg: JikanImageUrls | None = None
    webp: JikanImageUrls | None = None


class JikanTrailerImages(BaseModel):
    """Trailer thumbnail images at various sizes."""

    model_config = ConfigDict(extra="allow")

    image_url: str | None = None
    small_image_url: str | None = None
    medium_image_url: str | None = None
    large_image_url: str | None = None
    maximum_image_url: str | None = None


class JikanTrailer(BaseModel):
    """YouTube trailer info embedded in anime responses."""

    youtube_id: str | None = None
    url: str | None = None
    embed_url: str | None = None
    images: JikanTrailerImages | None = None


class JikanTitleEntry(BaseModel):
    """A single title variant (e.g. Default, English, Japanese, Synonym).

    The `titles` array on an anime contains multiple of these — one per
    language/variant. This is the canonical source for title data; the
    flat `title_english`/`title_japanese` fields are convenience copies.
    """

    type: str
    title: str


class JikanEntityReference(BaseModel):
    """A lightweight reference to a shared entity (genre, studio, producer, etc.).

    These appear in arrays like `genres`, `studios`, `producers` on an anime.
    Each has its own MAL ID and can be shared across many anime.
    """

    mal_id: int
    type: str
    name: str
    url: str


class JikanAiredProp(BaseModel):
    """Structured date parts within the `aired.prop` object."""

    model_config = ConfigDict(extra="allow")

    day: int | None = None
    month: int | None = None
    year: int | None = None


class JikanAiredPropContainer(BaseModel):
    """The `prop` sub-object inside `aired`, containing from/to date parts."""

    model_config = ConfigDict(extra="allow")

    # "from" is a Python reserved word — same handling as JikanAired
    from_prop: JikanAiredProp | None = None
    to: JikanAiredProp | None = None
    string: str | None = None

    def __init__(self, **data: object) -> None:
        if "from" in data:
            data["from_prop"] = data.pop("from")
        super().__init__(**data)


class JikanAired(BaseModel):
    """Airing date range for an anime.

    `from` and `to` are ISO 8601 datetime strings (nullable).
    `prop` contains the same dates broken into day/month/year ints.
    `string` is a human-readable date range like "Apr 3, 1998 to Apr 24, 1999".
    """

    # "from" is a Python reserved word — Jikan uses it as a JSON key.
    # Pydantic's alias handles the mapping.
    from_date: str | None = None
    to: str | None = None
    prop: JikanAiredPropContainer | None = None
    string: str | None = None

    model_config = ConfigDict(populate_by_name=True)

    def __init__(self, **data: object) -> None:
        # Map the JSON key "from" → our field "from_date"
        if "from" in data:
            data["from_date"] = data.pop("from")
        super().__init__(**data)


class JikanBroadcast(BaseModel):
    """Broadcast schedule info (for currently airing TV anime)."""

    day: str | None = None
    time: str | None = None
    timezone: str | None = None
    string: str | None = None


# ---------------------------------------------------------------------------
# Core anime data
# ---------------------------------------------------------------------------


class JikanAnimeData(BaseModel):
    """A single anime entry from the Jikan API.

    This mirrors the object found at `data` in a single-anime response,
    or each item in `data[]` for paginated listing responses.

    All fields are typed to match what Jikan actually returns, with
    nullable fields for data that isn't always present (ongoing series
    have no episode count, unscored entries have no score, etc.).
    """

    model_config = ConfigDict(extra="allow")

    # --- Identity ---
    mal_id: int
    url: str
    images: JikanImages | None = None
    trailer: JikanTrailer | None = None
    approved: bool | None = None

    # --- Titles ---
    # The `titles` array is the canonical source; flat fields are convenience copies
    titles: list[JikanTitleEntry] = []
    title: str | None = None
    title_english: str | None = None
    title_japanese: str | None = None
    title_synonyms: list[str] = []

    # --- Classification ---
    # "type" and "source" are Jikan's names. We rename them in the DB layer
    # to avoid SQL reserved words and confusion with our "source" concept.
    type: str | None = None
    source: str | None = None
    status: str | None = None
    rating: str | None = None

    # --- Metrics ---
    episodes: int | None = None
    score: float | None = None
    scored_by: int | None = None
    rank: int | None = None
    popularity: int | None = None
    members: int | None = None
    favorites: int | None = None

    # --- Airing ---
    airing: bool | None = None
    aired: JikanAired | None = None
    duration: str | None = None
    season: str | None = None
    year: int | None = None
    broadcast: JikanBroadcast | None = None

    # --- Content ---
    synopsis: str | None = None
    background: str | None = None

    # --- Related entities (shared across anime) ---
    producers: list[JikanEntityReference] = []
    licensors: list[JikanEntityReference] = []
    studios: list[JikanEntityReference] = []
    genres: list[JikanEntityReference] = []
    explicit_genres: list[JikanEntityReference] = []
    themes: list[JikanEntityReference] = []
    demographics: list[JikanEntityReference] = []


# ---------------------------------------------------------------------------
# Pagination
# ---------------------------------------------------------------------------


class JikanPaginationItems(BaseModel):
    """Item counts within a paginated response."""

    count: int
    total: int
    per_page: int


class JikanPagination(BaseModel):
    """Pagination metadata from Jikan list endpoints."""

    last_visible_page: int
    has_next_page: bool
    current_page: int | None = None
    items: JikanPaginationItems | None = None


# ---------------------------------------------------------------------------
# Top-level response wrappers
# ---------------------------------------------------------------------------


class JikanAnimeResponse(BaseModel):
    """Response from GET /anime/{id} — a single anime.

    Use this to validate the full API response including the `data` wrapper.
    """

    data: JikanAnimeData


class JikanAnimeListResponse(BaseModel):
    """Response from GET /anime?... — a paginated list of anime.

    Contains both the data array and pagination metadata.
    """

    pagination: JikanPagination
    data: list[JikanAnimeData]
