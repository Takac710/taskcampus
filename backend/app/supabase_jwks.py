"""Fetches and caches Supabase's JWKS.

Newer Supabase projects sign Auth JWTs with an asymmetric key pair (ES256)
by default; only older projects (or ones explicitly switched back) still
sign every token with the legacy shared HS256 secret. deps.py picks the
right verification path per-token based on its `alg` header -- this module
covers the asymmetric case.
"""

import time

import httpx

from .config import get_settings

settings = get_settings()

_CACHE_TTL_SECONDS = 3600.0
_cache: dict | None = None
_cache_fetched_at = 0.0


def get_jwks() -> dict:
    global _cache, _cache_fetched_at
    now = time.monotonic()
    if _cache is None or now - _cache_fetched_at > _CACHE_TTL_SECONDS:
        url = f"{settings.supabase_url.rstrip('/')}/auth/v1/.well-known/jwks.json"
        response = httpx.get(url, timeout=5.0)
        response.raise_for_status()
        _cache = response.json()
        _cache_fetched_at = now
    return _cache
