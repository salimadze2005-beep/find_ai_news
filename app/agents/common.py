from pathlib import Path

PROMPTS = Path(__file__).resolve().parents[2] / "prompts"


def ask(llm, role, data, schema):
    common = (PROMPTS / "common.md").read_text(encoding="utf-8")
    prompt = (PROMPTS / f"{role}.md").read_text(encoding="utf-8")
    return llm.generate_structured(role, common + "\n" + prompt, data, schema)


def source_data(sources, content=True):
    return [s.model_dump(mode="json", exclude=set() if content else {"content"}) for s in sources]
