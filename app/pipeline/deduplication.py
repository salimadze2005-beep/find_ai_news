import re
from difflib import SequenceMatcher
from app.models import Model
from app.agents.common import ask


class Groups(Model):
    groups: list[list[str]]


def normalized(text):
    return " ".join(re.findall(r"\w+", text.casefold()))


def compatible(a, b):
    entities_a, entities_b = {normalized(x) for x in a.entities}, {normalized(x) for x in b.entities}
    if a.event_kind != b.event_kind or not entities_a.intersection(entities_b):
        return False
    if a.published_at and b.published_at and abs((a.published_at - b.published_at).total_seconds()) > 48 * 3600:
        return False
    return True


def merge(a, b):
    sources = {s.url: s for s in a.sources + b.sources}
    return a.model_copy(update={"sources": list(sources.values()), "entities": sorted(set(a.entities + b.entities))})


def deduplicate(events, llm=None, trace=lambda *args: None):
    result = []
    for event in events:
        for index, old in enumerate(result):
            shared = {s.url for s in old.sources} & {s.url for s in event.sources}
            similarity = SequenceMatcher(None, normalized(old.title), normalized(event.title)).ratio()
            if compatible(old, event) and (similarity >= .88 or (shared and similarity >= .55)):
                result[index] = merge(old, event)
                trace("duplicate", {"removed": event.id, "kept": old.id, "method": "title/entity/date"})
                break
        else:
            result.append(event)
    if llm and len(result) > 1:
        proposal = ask(llm, "deduplication", {"events": [e.model_dump(mode="json", exclude={"sources"}) for e in result]}, Groups)
        by_id = {e.id: e for e in result}
        removed = set()
        for group in proposal.groups:
            if len(group) < 2 or len(set(group)) != len(group) or any(i not in by_id or i in removed for i in group):
                continue
            # Every pair must be compatible, avoiding transitive A-B-C overmerging.
            if not all(compatible(by_id[a], by_id[b]) for a in group for b in group):
                continue
            kept = group[0]
            for other in group[1:]:
                by_id[kept] = merge(by_id[kept], by_id[other])
                removed.add(other)
                trace("duplicate", {"removed": other, "kept": kept, "method": "semantic/entity/date"})
        result = [by_id[e.id] for e in result if e.id not in removed]
    trace("deduplicated", [e.model_dump(mode="json") for e in result])
    return result
