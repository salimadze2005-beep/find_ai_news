"""Run the real LLM/page pipeline on a curated public-source manifest, without Tavily."""
import argparse
import json
from datetime import datetime
from pathlib import Path
from app.config import Settings
from app.llm.provider import AgentRouterProvider
from app.models import NewsSource
from app.pipeline.orchestrator import run_pipeline
from app.render import render_digest, usage_totals
from app.search.base import SearchProvider
from app.search.pages import WebPages, domain


class ManifestSearch(SearchProvider):
    def __init__(self, manifest):
        self.sources = [NewsSource(title=item["title"], url=item["url"],
                                   snippet=item.get("snippet", ""), source=domain(item["url"]))
                        for item in manifest["sources"]]

    def search(self, query, start_date, end_date, limit):
        terms = {term.casefold().strip('"') for term in query.split() if len(term) > 3}
        ranked = sorted(self.sources, key=lambda source: sum(
            term in (source.title + " " + source.snippet).casefold() for term in terms), reverse=True)
        return ranked[:limit]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--output-prefix", type=Path, default=Path("data/curated-live"))
    parser.add_argument("--analysis-model", help="Optional model for verifier, analysts and editor")
    parser.add_argument("--as-of", type=datetime.fromisoformat,
                        help="Historical evaluation cutoff (ISO timestamp with timezone); default: current time")
    args = parser.parse_args()
    manifest = json.loads(args.manifest.read_text(encoding="utf-8-sig"))
    if args.as_of is not None and args.as_of.tzinfo is None:
        parser.error("--as-of must include a timezone")
    overrides = {role + "_model": args.analysis_model for role in ("verifier", "context", "impact", "editor")} if args.analysis_model else {}
    settings = Settings(mock_mode=False, search_queries_count=6, max_scout_results=20,
                        max_analysis_events=8, max_llm_calls=35, max_search_calls=40,
                        max_page_fetches=60, database_path=args.output_prefix.with_suffix(".sqlite3"),
                        **overrides)
    llm = AgentRouterProvider(settings)
    digest = run_pipeline(settings, now=args.as_of, injected=(llm, ManifestSearch(manifest), WebPages(60)),
                          progress=lambda message: print(message, flush=True))
    args.output_prefix.parent.mkdir(parents=True, exist_ok=True)
    args.output_prefix.with_suffix(".md").write_text(render_digest(digest), encoding="utf-8")
    args.output_prefix.with_suffix(".json").write_text(digest.model_dump_json(indent=2), encoding="utf-8")
    print(json.dumps({"run_id": digest.run_id, "events": len(digest.events),
                      "unconfirmed": len(digest.unconfirmed), "warnings": digest.warnings,
                      "usage": usage_totals(digest.usage)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
