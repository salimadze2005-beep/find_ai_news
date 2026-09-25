from pathlib import Path

PROMPTS = Path(__file__).resolve().parents[2] / "prompts"


def ask(llm, role, data, schema):
    common = (PROMPTS / "common.md").read_text(encoding="utf-8")
    prompt = (PROMPTS / f"{role}.md").read_text(encoding="utf-8")
    return llm.generate_structured(role, common + "\n" + prompt, data, schema)


def ask_validated(llm, role, data, schema, validate, trace):
    """One bounded domain-evidence repair; every call still uses the provider budget."""
    from app.llm.base import ProviderError
    request = dict(data)
    for attempt in range(2):
        result = ask(llm, role, request, schema)
        try:
            validate(result)
            return result
        except ProviderError as exc:
            trace("analysis_validation", {"agent": role, "attempt": attempt + 1, "error": str(exc)})
            if attempt:
                raise
            request = {**data, "previous_output": result.model_dump(mode="json"),
                "validation_feedback": {"error": str(exc), "instruction":
                    "Correct only the unsupported claims in previous_output. Preserve supported evidence. "
                    "Omit unsupported numbers, dates, version numbers and quantitative recommendations "
                    "from analytical prose. Do not add evidence or bypass the validation rule."}}


def source_data(sources, content=True):
    return [s.model_dump(mode="json", exclude=set() if content else {"content"}) for s in sources]
