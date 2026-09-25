"""Single-command CLI: python -m app.run [--mock] [--output digest.md]."""
import argparse
import sys
from pathlib import Path
from app.config import Settings
from app.pipeline.orchestrator import run_pipeline
from app.render import render_digest, render_html
from app.models import FinalDigest
from pydantic import ValidationError
from app.llm.base import ProviderError


def main():
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="AI Intelligence: evidence-first web research")
    parser.add_argument("--mock", action="store_true", help="Force offline synthetic demo")
    parser.add_argument("--output", type=Path, help="Write UTF-8 Markdown digest")
    parser.add_argument("--json", type=Path, help="Write structured digest")
    parser.add_argument("--html", type=Path, help="Write a standalone Russian report with expandable cards")
    parser.add_argument("--from-json", type=Path, help="Format a saved digest without search or model calls")
    args = parser.parse_args()
    try:
        if args.from_json:
            if args.mock:
                parser.error("--mock and --from-json cannot be combined")
            digest = FinalDigest.model_validate_json(args.from_json.read_text(encoding="utf-8"))
        else:
            settings = Settings()
            if args.mock:
                settings.mock_mode = True
            digest = run_pipeline(settings, progress=lambda s: print(s, file=sys.stderr))
    except (OSError, ValidationError):
        print("Не удалось прочитать отчёт или конфигурацию: проверьте файл и его формат.", file=sys.stderr)
        raise SystemExit(1) from None
    except ProviderError as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(1) from None
    markdown = render_digest(digest)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(markdown, encoding="utf-8")
    elif not args.html:
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8")
        print(markdown)
    if args.html:
        args.html.parent.mkdir(parents=True, exist_ok=True)
        args.html.write_text(render_html(digest), encoding="utf-8")
    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(digest.model_dump_json(indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
