import json
import time
from urllib.parse import urlsplit
import httpx
from pydantic import ValidationError
from app.llm.base import LLMProvider, ProviderError
from app.models import Usage


def strict_schema(schema):
    """OpenAI-compatible strict schemas require all object properties to be required."""
    if isinstance(schema, dict):
        schema = {k: strict_schema(v) for k, v in schema.items() if k != "default"}
        if schema.get("type") == "object" and "properties" in schema:
            schema["required"] = list(schema["properties"])
            schema["additionalProperties"] = False
    elif isinstance(schema, list):
        schema = [strict_schema(v) for v in schema]
    return schema


class AgentRouterProvider(LLMProvider):
    """Configurable chat/completions adapter; supports AgentRouter-compatible gateways."""
    def __init__(self, settings, client=None):
        super().__init__()
        self.settings = settings
        parts = urlsplit(settings.llm_base_url)
        if parts.scheme != "https" or not parts.hostname or parts.username or parts.query or parts.fragment:
            raise ProviderError("LLM_BASE_URL must be an HTTPS base URL without credentials/query")
        self.client = client or httpx.Client(timeout=90, trust_env=False)
        self.calls = 0

    def generate_structured(self, agent, system_prompt, input_data, response_schema):
        if self.calls >= self.settings.max_llm_calls:
            raise ProviderError("LLM call budget exhausted")
        payload = json.dumps(input_data, ensure_ascii=False, default=str)
        if len(payload) > self.settings.max_input_chars:
            raise ProviderError("LLM input exceeds configured character budget")
        self.calls += 1
        model = self.settings.model_for(agent)
        schema = response_schema.model_json_schema()
        fmt = {"type": "json_object"}
        if self.settings.llm_response_format == "json_schema":
            fmt = {"type": "json_schema", "json_schema": {
                "name": response_schema.__name__, "strict": True, "schema": strict_schema(schema)}}
        request = {"model": model, "messages": [
            {"role": "system", "content": system_prompt + "\nReturn only JSON matching this schema:\n" + json.dumps(schema)},
            {"role": "user", "content": payload}], "response_format": fmt,
            "max_tokens": self.settings.llm_max_output_tokens}
        began = time.monotonic()
        usage = Usage(agent=agent, model=model, success=False)
        try:
            response = self.client.post(self.settings.llm_base_url.rstrip("/") + "/chat/completions",
                headers={"Authorization": "Bearer " + self.settings.llm_api_key.get_secret_value()}, json=request)
            if response.status_code != 200:
                raise ProviderError(f"LLM HTTP {response.status_code}; inspect gateway configuration/limits")
            data = response.json()
            raw = data.get("usage") or {}
            usage.input_tokens = raw.get("prompt_tokens")
            usage.output_tokens = raw.get("completion_tokens")
            usage.total_tokens = raw.get("total_tokens")
            if usage.total_tokens is None and usage.input_tokens is not None and usage.output_tokens is not None:
                usage.total_tokens = usage.input_tokens + usage.output_tokens
            price = self.settings.model_prices.get(model)
            if price and usage.input_tokens is not None and usage.output_tokens is not None:
                usage.estimated_cost = (usage.input_tokens * price["input"] + usage.output_tokens * price["output"]) / 1_000_000
            choice = data["choices"][0]
            if choice.get("finish_reason") not in {None, "stop"}:
                raise ProviderError("LLM output was incomplete or refused")
            result = response_schema.model_validate_json(choice["message"]["content"])
            usage.success = True
            return result
        except (httpx.HTTPError, ValueError, KeyError, IndexError, TypeError, ValidationError) as exc:
            raise ProviderError(f"LLM request/JSON validation failed ({type(exc).__name__})") from None
        finally:
            usage.duration = round(time.monotonic() - began, 3)
            self.record(usage)
