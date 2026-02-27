# otakulogs-data

## What This Is

A personal data engineering project that builds a canonical ACGN (Anime, Comics, Games, Novels)
database by extracting and transforming data from public sources, then loading it into Supabase.

Starting with anime data from Jikan (MyAnimeList API wrapper), expanding to other sources
and media types over time.

## Public Repository

This repo is public on GitHub. Every file committed is visible to anyone.
Keep this in mind at all times:
- **Never commit secrets, credentials, or API keys.** Use `.context/` (gitignored) for local config.
- **Code should be self-documenting.** Verbose variable names, intentional step-by-step logic.
- **Comments explain "why", not "what".** The naming handles "what". Comments capture decisions,
  tradeoffs, and context that the code alone can't convey.
- **No premature abstractions.** Prefer explicit, readable steps over clever helpers. Three similar
  lines are better than a premature abstraction. This repo should be readable by someone learning.
- **Keep the code educational.** Someone should be able to read through the pipeline and understand
  both the data engineering concepts and the implementation.

## Tech Stack

- **Language:** Python 3.12+
- **Package manager:** uv
- **Database:** Supabase (PostgreSQL)
- **HTTP client:** httpx (async)
- **Type checking:** pyright (strict mode)
- **Linting:** ruff
- **Testing:** pytest + pytest-asyncio

## Project Structure

```
src/otakulogs_data/
├── sources/       # Data extraction — one module per source (jikan, anilist, etc.)
├── transforms/    # Cleaning, normalizing, mapping source data to canonical schema
├── loaders/       # Writing transformed data to Supabase
└── schema/        # Canonical data models and type definitions
```

- `scripts/` — Runnable entry points and exploration scripts
- `tests/` — Test suite
- `.context/` — Local-only files (gitignored): credentials, scratch notes

## Code Style

- **Type everything.** Pyright strict mode is enforced. All functions need parameter and return types.
- **Verbose naming.** `anime_title_in_english` over `title_en`. `raw_response_from_jikan` over `resp`.
- **Step-by-step logic.** Break operations into named intermediate variables rather than chaining.
  Each variable name documents what that step produces.
- **Strategic comments.** Explain architectural decisions, data source quirks, and non-obvious "why"s.
  Don't explain what the code does — the naming handles that.

## Git

- **Identity:** bryluke (bryluke000@gmail.com)
- **SSH:** Uses `github.com-bryluke` host alias
- **Repo:** bryluke/otakulogs-data (public)

## Workflow

Build features step by step. Each piece should be small enough to understand, test, and review:
1. Explore the data source (curl, scripts)
2. Design types/models based on what we see
3. Build the extractor
4. Build the transform
5. Build the loader
6. Test the full pipeline

## Local Context

Secrets and local configuration live in `.context/` (gitignored).
See `.context/notes.md` for Supabase credentials and API keys.
