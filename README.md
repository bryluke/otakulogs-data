# otakulogs-data

A data engineering project that builds a canonical ACGN (Anime, Comics, Games, Novels) database
from public data sources.

The goal is to consume, normalize, and unify data from multiple public APIs — starting with anime
data from [Jikan](https://jikan.moe) (a MyAnimeList API wrapper) — into a single canonical database
hosted on [Supabase](https://supabase.com) (PostgreSQL).

## Why This Exists

This project serves two purposes:

1. **Learning data engineering.** Building real ETL (Extract, Transform, Load) pipelines from
   scratch — dealing with rate limits, inconsistent schemas, entity resolution across sources,
   and all the messy realities of working with external data.

2. **Building a foundation.** The canonical database produced here will power future applications
   (a backlog tracker, recommendation engine, social features, public API). This repo is the
   data layer — the single source of truth.

## What's an ACGN Database?

ACGN stands for **Anime, Comics, Games, Novels** — the four pillars of East Asian pop culture
media. Public databases like [MyAnimeList](https://myanimelist.net),
[AniList](https://anilist.co), and [AniDB](https://anidb.net) each maintain their own catalogs
with overlapping but inconsistent data.

This project extracts from these sources and builds a **canonical record** — one unified entry per
anime/manga/game/novel that reconciles differences across sources.

## Tech Stack

| Tool | Purpose |
|------|---------|
| Python 3.12+ | Language |
| [uv](https://docs.astral.sh/uv/) | Package and environment management |
| [httpx](https://www.python-httpx.org/) | Async HTTP client for API calls |
| [Supabase](https://supabase.com) | PostgreSQL database (hosted) |
| [pyright](https://github.com/microsoft/pyright) | Static type checking (strict mode) |
| [ruff](https://docs.astral.sh/ruff/) | Linting and formatting |
| [pytest](https://docs.pytest.org/) | Testing |

## Getting Started

### Prerequisites

- Python 3.12 or higher
- [uv](https://docs.astral.sh/uv/) (Python package manager)

Install uv if you don't have it:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Setup

Clone the repo and install dependencies:

```bash
git clone git@github.com:bryluke/otakulogs-data.git
cd otakulogs-data
uv sync
```

This creates a `.venv` virtual environment and installs all dependencies (including dev tools).

### Running Scripts

Use `uv run` to execute scripts within the virtual environment:

```bash
uv run python scripts/explore_jikan.py
```

`uv run` automatically activates the virtual environment — no need to manually source `.venv/bin/activate`.

### Type Checking and Linting

```bash
uv run pyright              # static type checking (strict mode)
uv run ruff check .         # lint
uv run ruff format .        # auto-format
uv run pytest               # run tests
```

## Project Structure

```
otakulogs-data/
├── src/otakulogs_data/     # Main package
│   ├── sources/            # Data extraction (one module per API source)
│   ├── transforms/         # Cleaning, normalizing, deduplication
│   ├── loaders/            # Loading data into Supabase
│   └── schema/             # Canonical data models and types
├── scripts/                # Runnable exploration and pipeline scripts
├── tests/                  # Test suite
├── pyproject.toml          # Project config, dependencies, tool settings
└── CLAUDE.md               # AI assistant context file
```

## Data Sources

| Source | Status | Type | Notes |
|--------|--------|------|-------|
| [Jikan](https://jikan.moe) | In progress | REST API | Unofficial MAL wrapper. Rate-limited. Starting here. |
| [AniList](https://anilist.co) | Planned | GraphQL API | Clean API, good docs. |
| [MyAnimeList](https://myanimelist.net/apiconfig/references/api/v2) | Planned | REST API | Official. Requires OAuth. |
| [AniDB](https://anidb.net) | Planned | HTTP API | Most granular metadata. Stricter access. |
| [Kitsu](https://kitsu.docs.apiary.io) | Planned | JSON:API | Good for cross-referencing. |

## License

This project is for educational and personal use. Data sourced from public APIs is subject to
their respective terms of service.
