"""A small shared ``requests`` session with a User-Agent and retries."""

from __future__ import annotations

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from .. import config

_session: requests.Session | None = None


def session() -> requests.Session:
    """Return a process-wide session with sane retry/back-off behaviour."""
    global _session
    if _session is not None:
        return _session

    s = requests.Session()
    s.headers.update({"User-Agent": config.USER_AGENT, "Accept": "application/json"})
    retry = Retry(
        total=3,
        backoff_factor=0.5,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=("GET",),
        raise_on_status=False,
    )
    adapter = HTTPAdapter(max_retries=retry)
    s.mount("https://", adapter)
    s.mount("http://", adapter)
    _session = s
    return s


def get_json(url: str, **kwargs) -> dict | list:
    resp = session().get(url, timeout=config.HTTP_TIMEOUT, **kwargs)
    resp.raise_for_status()
    return resp.json()
