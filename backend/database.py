"""Lightweight Supabase PostgREST client using httpx (no supabase-py dependency)."""
import json
import httpx
from backend.config import SUPABASE_URL, SUPABASE_KEY


class _Result:
    """Mimics supabase-py response shape."""
    def __init__(self, data):
        self.data = data


class _Query:
    """Chainable PostgREST query builder."""
    def __init__(self, url: str, headers: dict, table: str):
        self._base = f"{url}/rest/v1/{table}"
        self._headers = headers
        self._params: dict = {}
        self._body = None
        self._method = "GET"
        self._single = False

    def select(self, columns: str = "*") -> "_Query":
        self._method = "GET"
        self._params["select"] = columns
        return self

    def insert(self, data: dict) -> "_Query":
        self._method = "POST"
        self._body = data
        self._headers["Prefer"] = "return=representation"
        return self

    def update(self, data: dict) -> "_Query":
        self._method = "PATCH"
        self._body = data
        self._headers["Prefer"] = "return=representation"
        return self

    def eq(self, column: str, value) -> "_Query":
        self._params[column] = f"eq.{value}"
        return self

    def order(self, column: str, desc: bool = False) -> "_Query":
        direction = "desc" if desc else "asc"
        self._params["order"] = f"{column}.{direction}"
        return self

    def single(self) -> "_Query":
        self._single = True
        self._headers["Accept"] = "application/vnd.pgrst.object+json"
        return self

    def execute(self) -> _Result:
        with httpx.Client(timeout=30.0) as client:
            if self._method == "GET":
                r = client.get(self._base, headers=self._headers, params=self._params)
            elif self._method == "POST":
                r = client.post(self._base, headers=self._headers, params=self._params, json=self._body)
            elif self._method == "PATCH":
                r = client.patch(self._base, headers=self._headers, params=self._params, json=self._body)
            else:
                raise ValueError(f"Unknown method: {self._method}")

            r.raise_for_status()
            data = r.json()
            return _Result(data if isinstance(data, list) else (data if self._single else [data]))


class _SupabaseClient:
    def __init__(self, url: str, key: str):
        self._url = url
        self._headers = {
            "apikey": key,
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
        }

    def table(self, name: str) -> _Query:
        return _Query(self._url, dict(self._headers), name)


_client: _SupabaseClient | None = None


def get_supabase() -> _SupabaseClient:
    global _client
    if _client is None:
        _client = _SupabaseClient(SUPABASE_URL, SUPABASE_KEY)
    return _client
