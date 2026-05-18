"""
systems/utils/github_store.py
GitHub-backed JSON storage.

When GITHUB_TOKEN is present in Streamlit secrets, all data is read from
and written to the GitHub repository via the API — so data persists across
every Streamlit Cloud redeployment.

When GITHUB_TOKEN is absent (local development), falls back to the local
filesystem exactly as before.
"""

from __future__ import annotations

import base64
import json
from pathlib import Path
from typing import Any, Callable

import requests
import streamlit as st

_OWNER  = "emadsamirzaki"
_REPO   = "ArkPanel"
_BRANCH = "master"
_BASE   = f"https://api.github.com/repos/{_OWNER}/{_REPO}/contents"


def _token() -> str | None:
    try:
        return st.secrets["GITHUB_TOKEN"]
    except (KeyError, FileNotFoundError, AttributeError):
        return None


def _headers(token: str) -> dict:
    return {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json",
    }


def read_json(repo_path: str, local_path: Path, default: Any) -> Any:
    """Return parsed JSON — from GitHub if configured, else from local file."""
    token = _token()
    if token:
        r = requests.get(
            f"{_BASE}/{repo_path}",
            headers=_headers(token),
            params={"ref": _BRANCH},
            timeout=10,
        )
        if r.status_code == 404:
            return default
        r.raise_for_status()
        content = base64.b64decode(r.json()["content"]).decode("utf-8")
        return json.loads(content)
    # ── local fallback ────────────────────────────────────────────────────────
    if not local_path.exists():
        return default
    return json.loads(local_path.read_text(encoding="utf-8"))


def write_json(
    repo_path: str,
    local_path: Path,
    data: Any,
    message: str = "Update data",
    json_default: Callable | None = None,
) -> None:
    """Write JSON — to GitHub if configured, else to local file."""
    serialized = json.dumps(data, indent=2, ensure_ascii=False, default=json_default)
    token = _token()
    if token:
        content_b64 = base64.b64encode(serialized.encode("utf-8")).decode("utf-8")
        # Fetch current SHA (needed to update an existing file)
        r = requests.get(
            f"{_BASE}/{repo_path}",
            headers=_headers(token),
            params={"ref": _BRANCH},
            timeout=10,
        )
        payload: dict = {
            "message": message,
            "content": content_b64,
            "branch":  _BRANCH,
        }
        if r.status_code == 200:
            payload["sha"] = r.json()["sha"]
        r = requests.put(
            f"{_BASE}/{repo_path}",
            headers=_headers(token),
            json=payload,
            timeout=15,
        )
        r.raise_for_status()
        return
    # ── local fallback ────────────────────────────────────────────────────────
    local_path.parent.mkdir(exist_ok=True)
    local_path.write_text(serialized, encoding="utf-8")
