"""
Dünner Wrapper um die Notion API (Version 2025-09-03, Data-Sources-Modell).
Alle Aufrufe laufen serverseitig - der Integration-Token verlässt nie den Server.
"""
import os
import requests

NOTION_TOKEN = os.environ.get("NOTION_TOKEN", "")
NOTION_VERSION = "2025-09-03"
BASE_URL = "https://api.notion.com/v1"

# Data-Source-IDs deiner bestehenden Notion-Datenbanken
DS_SESSIONS = os.environ.get("DS_SESSIONS", "4656ab26-ea9d-4c2c-8b5a-b34027585259")
DS_EXERCISES = os.environ.get("DS_EXERCISES", "50b94877-f53d-4816-876e-76a9d9bdb763")
DS_BODYWEIGHT = os.environ.get("DS_BODYWEIGHT", "818c8f6f-69eb-4516-9454-7998a1948ba2")


def _headers():
    return {
        "Authorization": f"Bearer {NOTION_TOKEN}",
        "Notion-Version": NOTION_VERSION,
        "Content-Type": "application/json",
    }


class NotionError(Exception):
    pass


def _check(resp):
    if resp.status_code >= 400:
        raise NotionError(f"Notion API Fehler {resp.status_code}: {resp.text[:500]}")
    return resp.json()


# ---------- Query ----------

def query_data_source(data_source_id, filter=None, sorts=None, page_size=100):
    """Fragt alle Seiten (Zeilen) einer Notion-Data-Source ab, inkl. Pagination."""
    results = []
    body = {"page_size": page_size}
    if filter:
        body["filter"] = filter
    if sorts:
        body["sorts"] = sorts

    cursor = None
    while True:
        if cursor:
            body["start_cursor"] = cursor
        resp = requests.post(
            f"{BASE_URL}/data_sources/{data_source_id}/query",
            headers=_headers(), json=body, timeout=20,
        )
        data = _check(resp)
        results.extend(data.get("results", []))
        if data.get("has_more"):
            cursor = data.get("next_cursor")
        else:
            break
    return results


def get_page(page_id):
    resp = requests.get(f"{BASE_URL}/pages/{page_id}", headers=_headers(), timeout=20)
    return _check(resp)


def create_page(data_source_id, properties):
    body = {
        "parent": {"type": "data_source_id", "data_source_id": data_source_id},
        "properties": properties,
    }
    resp = requests.post(f"{BASE_URL}/pages", headers=_headers(), json=body, timeout=20)
    return _check(resp)


def update_page(page_id, properties=None, archived=None):
    body = {}
    if properties is not None:
        body["properties"] = properties
    if archived is not None:
        body["archived"] = archived
    resp = requests.patch(f"{BASE_URL}/pages/{page_id}", headers=_headers(), json=body, timeout=20)
    return _check(resp)


# ---------- Property-Value-Helfer (Notion erwartet ein bestimmtes JSON-Format je Typ) ----------

def title_prop(text):
    return {"title": [{"text": {"content": text or ""}}]}


def rich_text_prop(text):
    return {"rich_text": [{"text": {"content": text or ""}}]} if text else {"rich_text": []}


def number_prop(value):
    return {"number": float(value) if value not in (None, "") else None}


def date_prop(iso_date):
    return {"date": {"start": iso_date}} if iso_date else {"date": None}


def select_prop(name):
    return {"select": {"name": name}} if name else {"select": None}


def multi_select_prop(names):
    names = [n for n in (names or []) if n]
    return {"multi_select": [{"name": n} for n in names]}


def relation_prop(page_ids):
    page_ids = [p for p in (page_ids or []) if p]
    return {"relation": [{"id": p} for p in page_ids]}


def url_prop(url):
    return {"url": url or None}


# ---------- Property-Value-Extraktion (Notion-Response -> einfache Python-Werte) ----------

def _plain_text(rich_text_list):
    return "".join([t.get("plain_text", "") for t in (rich_text_list or [])])


def extract_properties(page):
    """Wandelt die properties eines Notion-Page-Objekts in ein flaches dict um."""
    out = {"id": page["id"], "url": page.get("url")}
    for name, prop in page.get("properties", {}).items():
        ptype = prop.get("type")
        if ptype == "title":
            out[name] = _plain_text(prop.get("title"))
        elif ptype == "rich_text":
            out[name] = _plain_text(prop.get("rich_text"))
        elif ptype == "number":
            out[name] = prop.get("number")
        elif ptype == "date":
            d = prop.get("date")
            out[name] = d.get("start") if d else None
        elif ptype == "select":
            s = prop.get("select")
            out[name] = s.get("name") if s else None
        elif ptype == "multi_select":
            out[name] = [o.get("name") for o in prop.get("multi_select", [])]
        elif ptype == "relation":
            out[name] = [r.get("id") for r in prop.get("relation", [])]
        elif ptype == "url":
            out[name] = prop.get("url")
        elif ptype == "checkbox":
            out[name] = prop.get("checkbox")
        else:
            out[name] = None
    return out
