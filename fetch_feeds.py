"""Henter RSS-feeds og gemmer overskrifter, links og tidspunkter i feeds.json.
Gemmer kun titel, link og tid. Ingen artikeltekst.
Ret listen FEEDS for at tilføje eller fjerne feeds."""
import json, sys, urllib.request, urllib.error
import xml.etree.ElementTree as ET
from email.utils import parsedate_to_datetime
from datetime import datetime, timezone

FEEDS = [
    ("DR", "Seneste nyt", "https://www.dr.dk/nyheder/service/feeds/senestenyt"),
    ("DR", "Alle nyheder", "https://www.dr.dk/nyheder/service/feeds/allenyheder"),
    ("DR", "Indland", "https://www.dr.dk/nyheder/service/feeds/indland"),
    ("DR", "Udland", "https://www.dr.dk/nyheder/service/feeds/udland"),
    ("DR", "Politik", "https://www.dr.dk/nyheder/service/feeds/politik"),
    ("DR", "Penge", "https://www.dr.dk/nyheder/service/feeds/penge"),
    ("Ekstra Bladet", "Seneste", "https://ekstrabladet.dk/rssfeed/all/"),
    ("Ekstra Bladet", "Nyheder", "https://ekstrabladet.dk/rssfeed/nyheder/"),
    ("BT", "Nyheder", "https://www.bt.dk/nyheder/seneste/rss"),
    ("BT", "Seneste", "https://www.bt.dk/bt/seneste/rss"),
]
MAX_PER_FEED = 15
UA = "dagens-oversigt-rss/1.0 (privat nyhedsoverblik; hentes hvert kvarter)"

def iso(text):
    if not text:
        return None
    try:
        dt = parsedate_to_datetime(text.strip())
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc).isoformat(timespec="minutes")
    except Exception:
        return None

def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/rss+xml, application/xml, text/xml"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.status, r.read()

def parse(body):
    root = ET.fromstring(body)
    items = []
    for it in root.iter("item"):
        title = (it.findtext("title") or "").strip()
        link = (it.findtext("link") or "").strip()
        if not title or not link.startswith("https://"):
            continue
        items.append({"title": title, "link": link, "published": iso(it.findtext("pubDate"))})
    return items[:MAX_PER_FEED]

def main():
    out = {"generated": datetime.now(timezone.utc).isoformat(timespec="minutes"), "feeds": []}
    for source, name, url in FEEDS:
        entry = {"source": source, "name": name, "url": url, "status": "ok", "items": []}
        try:
            code, body = fetch(url)
            entry["items"] = parse(body)
            if not entry["items"]:
                entry["status"] = "tomt feed"
        except urllib.error.HTTPError as e:
            entry["status"] = f"HTTP {e.code}"
        except Exception as e:
            entry["status"] = f"fejl: {type(e).__name__}"
        print(f"{name}: {entry['status']} ({len(entry['items'])} punkter)")
        out["feeds"].append(entry)
    with open("feeds.json", "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)

if __name__ == "__main__":
    sys.exit(main())
