"""Reproducible, no-key live page/date audit. This does not simulate LLM execution."""
import argparse
import json
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
from pathlib import Path
from app.models import NewsSource, utcnow
from app.search.pages import WebPages, in_window


def audit_source(item, start, end):
    pages = WebPages(max_fetches=1)
    try:
        source = pages.fetch(NewsSource(title=item["title"], url=item["url"]))
        return {"id": item["id"], "url": item["url"], "purpose": item["purpose"],
            "fetched": source.fetched, "characters": len(source.content),
            "published_at": source.published_at.isoformat() if source.published_at else None,
            "precision": source.date_precision, "date_evidence": source.date_evidence,
            "in_window": in_window(source, start, end), "error": source.fetch_error}
    finally:
        pages.client.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--output", type=Path, default=Path("data/real-source-audit.json"))
    args = parser.parse_args()
    manifest = json.loads(args.manifest.read_text(encoding="utf-8-sig"))
    end = datetime.fromisoformat(manifest["as_of"].replace("Z", "+00:00"))
    start = end - timedelta(hours=manifest["lookback_hours"])
    with ThreadPoolExecutor(max_workers=3) as pool:
        rows = list(pool.map(lambda item: audit_source(item, start, end), manifest["sources"]))
    report = {"method": manifest["method"], "retrieved_at": utcnow().isoformat(),
              "window_start": start.isoformat(), "window_end": end.isoformat(), "sources": rows}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=True, indent=2))


if __name__ == "__main__":
    main()
