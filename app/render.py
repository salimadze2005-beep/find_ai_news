import re


def safe(text):
    return re.sub(r"([\\`*_{}\[\]<>()#!|])", r"\\\1", str(text))


def evidence_lines(items, label):
    lines = []
    if items:
        lines.append(f"### {label}")
        for item in items:
            refs = " ".join(f"[источник {i+1}](<{u}>)" for i, u in enumerate(item.source_urls))
            status = f"{item.status}: " if hasattr(item, "status") else ""
            lines.append(f"- {status}{safe(item.text)} {refs}")
    return lines


def usage_totals(usage):
    return {"input_tokens": sum(u.input_tokens or 0 for u in usage),
        "output_tokens": sum(u.output_tokens or 0 for u in usage),
        "total_tokens": sum(u.total_tokens or 0 for u in usage),
        "known_cost": sum(u.estimated_cost or 0 for u in usage),
        "calls": len(usage), "unknown_usage_calls": sum(u.total_tokens is None for u in usage),
        "unknown_cost_calls": sum(u.estimated_cost is None for u in usage),
        "duration": round(sum(u.duration for u in usage), 2)}


def render_digest(digest):
    from app.report import render_report
    return render_report(digest)


def render_html(digest):
    from app.report import render_report
    return render_report(digest, html=True)
