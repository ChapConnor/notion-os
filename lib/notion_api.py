"""Shared Notion client over requests — no SDK (§2.1.6).

Policy, exactly as ratified:
- token bucket ≤3 req/s
- 429: honor Retry-After, else exponential 1/2/4…60 s, max 5 retries
- 502/503/504/connection error: retried once
- 400/401/403/404: NEVER retried — immediate loud abort (401 names the
  rotation runbook; 400 surfaces Notion's validation message, which names
  the property)
- write failures abort the run: a skipped ledger write is a broken
  invariant (unlike garmin_io's skip-and-continue, right for health
  metrics and wrong for money)
"""
from __future__ import annotations

import logging
import time
from typing import Any, Iterator

import requests

from cfg import load, notion_token

API_BASE = "https://api.notion.com/v1"
MIN_REQUEST_INTERVAL = 1.0 / 3.0
MAX_429_RETRIES = 5
BACKOFF_CAP_S = 60

log = logging.getLogger(__name__)


class NotionAbort(SystemExit):
    """Non-retryable API failure. Aborts the run, loudly."""


class Notion:
    def __init__(self, token: str | None = None, version: str | None = None):
        config = load()
        self._token = token or notion_token()
        self._version = version or str(config["notion"]["version"])
        self._session = requests.Session()
        self._session.headers.update(
            {
                "Authorization": f"Bearer {self._token}",
                "Notion-Version": self._version,
                "Content-Type": "application/json",
            }
        )
        self._last_request = 0.0

    def _throttle(self) -> None:
        wait = self._last_request + MIN_REQUEST_INTERVAL - time.monotonic()
        if wait > 0:
            time.sleep(wait)
        self._last_request = time.monotonic()

    def request(self, method: str, path: str, payload: dict | None = None) -> dict:
        retries_429 = 0
        conn_retried = False
        backoff = 1
        while True:
            self._throttle()
            try:
                resp = self._session.request(
                    method, f"{API_BASE}{path}", json=payload, timeout=30
                )
            except requests.RequestException as exc:
                if conn_retried:
                    raise NotionAbort(f"connection error on {path} (after one retry): {exc}")
                conn_retried = True
                log.warning("connection error on %s: %s — retrying once", path, exc)
                time.sleep(5)
                continue

            if resp.status_code == 200:
                return resp.json()

            if resp.status_code == 429:
                if retries_429 >= MAX_429_RETRIES:
                    raise NotionAbort(f"429 on {path}: exhausted {MAX_429_RETRIES} retries")
                retry_after = resp.headers.get("Retry-After")
                delay = float(retry_after) if retry_after else min(backoff, BACKOFF_CAP_S)
                backoff *= 2
                retries_429 += 1
                log.warning("429 on %s — sleeping %.1fs (retry %d)", path, delay, retries_429)
                time.sleep(delay)
                continue

            if resp.status_code in (502, 503, 504):
                if conn_retried:
                    raise NotionAbort(f"{resp.status_code} on {path} (after one retry)")
                conn_retried = True
                log.warning("%d on %s — retrying once", resp.status_code, path)
                time.sleep(5)
                continue

            # 400/401/403/404 and anything else: never retried.
            detail = ""
            try:
                detail = resp.json().get("message", "")
            except ValueError:
                pass
            if resp.status_code == 401:
                raise NotionAbort(
                    "Notion API 401 unauthorized — token dead or rotated. "
                    "Runbook: 'Notion token rotation' (README §2.5.2): regenerate "
                    "at notion.so/my-integrations, paste into "
                    "~/.config/notion-os/notion.env, re-run with --dry-run."
                )
            raise NotionAbort(f"Notion API {resp.status_code} on {path}: {detail}")

    # ---- paginated reads -------------------------------------------------

    def query_db(
        self,
        db_id: str,
        filter: dict | None = None,
        sorts: list | None = None,
    ) -> Iterator[dict]:
        payload: dict[str, Any] = {"page_size": 100}
        if filter:
            payload["filter"] = filter
        if sorts:
            payload["sorts"] = sorts
        cursor: str | None = None
        while True:
            if cursor:
                payload["start_cursor"] = cursor
            data = self.request("POST", f"/databases/{db_id}/query", payload)
            yield from data.get("results", [])
            if not data.get("has_more"):
                return
            cursor = data.get("next_cursor")

    # ---- writes ----------------------------------------------------------

    def create_page(
        self, db_id: str, properties: dict, children: list | None = None
    ) -> dict:
        payload: dict[str, Any] = {
            "parent": {"database_id": db_id},
            "properties": properties,
        }
        if children:
            payload["children"] = children
        return self.request("POST", "/pages", payload)

    def update_page(self, page_id: str, properties: dict) -> dict:
        return self.request("PATCH", f"/pages/{page_id}", {"properties": properties})


# ---- property helpers (build/read the JSON shapes in one place) ----------

def title(text: str | None) -> dict:
    return {"title": [{"text": {"content": text}}] if text else []}


def rich_text(text: str | None) -> dict:
    return {"rich_text": [{"text": {"content": text}}] if text else []}


def number(value: float | int | None) -> dict:
    return {"number": value}


def date_prop(iso: str | None) -> dict:
    return {"date": {"start": iso} if iso else None}


def select(name: str | None) -> dict:
    return {"select": {"name": name} if name else None}


def relation(page_ids: list[str]) -> dict:
    return {"relation": [{"id": pid} for pid in page_ids]}


def read_title(page: dict, prop: str) -> str:
    return "".join(t.get("plain_text", "") for t in page["properties"][prop]["title"])


def read_date(page: dict, prop: str) -> str | None:
    d = page["properties"][prop].get("date")
    return d["start"] if d else None


def read_select(page: dict, prop: str) -> str | None:
    s = page["properties"][prop].get("select")
    return s["name"] if s else None


def read_number(page: dict, prop: str) -> float | None:
    return page["properties"][prop].get("number")
