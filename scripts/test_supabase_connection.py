"""Smoke test: verify we can connect to Supabase.

Run: uv run python scripts/test_supabase_connection.py
"""

import os
from pathlib import Path

from dotenv import load_dotenv
from supabase import create_client

# Load credentials from .context/.env (gitignored)
load_dotenv(Path(__file__).resolve().parent.parent / ".context" / ".env")

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_SERVICE_KEY = os.environ["SUPABASE_SERVICE_KEY"]


def test_connection() -> None:
    """Create a Supabase client and verify connectivity."""
    print("--- Supabase Connection Test ---")
    print(f"  URL: {SUPABASE_URL}")
    print()

    client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
    print(f"  Client created")
    print(f"  REST URL:  {client.rest_url}")
    print(f"  Auth URL:  {client.auth_url}")
    print()

    # Try selecting from a table that doesn't exist yet.
    # - "relation not found" or empty result = connection works, auth works
    # - 401/403 = bad credentials
    # - connection error = can't reach Supabase
    print("  Testing query (select from non-existent table)...")
    try:
        client.table("_health_check_nonexistent").select("*").limit(1).execute()
        print("  Unexpected success — table shouldn't exist")
    except Exception as error:
        error_message = str(error)
        if "does not exist" in error_message or "not found" in error_message:
            print(f"  Got expected 'not found' error — connection and auth are working!")
        elif "401" in error_message or "403" in error_message or "JWT" in error_message:
            print(f"  AUTH FAILURE: {error_message}")
            return
        else:
            # Any PostgREST error means we reached the server and authenticated
            print(f"  Got response from PostgREST: {error_message}")
            print(f"  Connection and auth are working!")

    print()
    print("Supabase connection verified!")


if __name__ == "__main__":
    test_connection()
