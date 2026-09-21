from pathlib import Path
from pydantic import Field, SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    mock_mode: bool = True
    lookback_hours: int = Field(48, ge=1, le=168)
    min_significance_score: float = Field(6.5, ge=0, le=10)
    max_scout_results: int = Field(30, ge=1, le=100)
    max_analysis_events: int = Field(12, ge=1, le=30)
    search_queries_count: int = Field(8, ge=3, le=16)
    verify_sources_min: int = Field(2, ge=2, le=5)
    verify_sources_target: int = Field(3, ge=2, le=8)
    scoring_weights: dict[str, float] = Field(default_factory=lambda: {
        "importance": .30, "impact": .25, "practicality": .20, "novelty": .15, "confidence": .10})
    llm_model: str = "configure-model-id"
    scout_model: str = ""
    verifier_model: str = ""
    context_model: str = ""
    impact_model: str = ""
    editor_model: str = ""
    llm_base_url: str = "https://agentrouter.org/v1"
    llm_api_key: SecretStr = SecretStr("")
    tavily_api_key: SecretStr = SecretStr("")
    llm_response_format: str = "json_object"
    llm_max_output_tokens: int = Field(6000, ge=512, le=16000)
    max_llm_calls: int = Field(80, ge=1, le=200)
    max_search_calls: int = Field(80, ge=1, le=200)
    max_page_fetches: int = Field(80, ge=1, le=200)
    max_input_chars: int = Field(70000, ge=4000, le=150000)
    # Per model USD / million tokens: {"model": {"input": 0.1, "output": 0.4}}
    model_prices: dict[str, dict[str, float]] = Field(default_factory=dict)
    database_path: Path = Path("data/intelligence.sqlite3")
    enable_alfa_relevance: bool = False

    @model_validator(mode="after")
    def validate_settings(self):
        expected = {"importance", "impact", "practicality", "novelty", "confidence"}
        if set(self.scoring_weights) != expected or any(v < 0 for v in self.scoring_weights.values()):
            raise ValueError("Scoring weights must contain five nonnegative dimensions")
        if abs(sum(self.scoring_weights.values()) - 1) > 1e-6:
            raise ValueError("Scoring weights must sum to 1")
        if self.verify_sources_target < self.verify_sources_min:
            raise ValueError("Target sources must be >= minimum")
        if self.llm_response_format not in {"json_object", "json_schema"}:
            raise ValueError("LLM_RESPONSE_FORMAT must be json_object or json_schema")
        for price in self.model_prices.values():
            if set(price) != {"input", "output"} or any(v < 0 for v in price.values()):
                raise ValueError("Model prices require nonnegative input and output rates")
        return self

    def model_for(self, agent: str) -> str:
        role = {"queries": "scout", "deduplication": "scout", "context_analyst": "context",
                "impact_analyst": "impact"}.get(agent, agent)
        return getattr(self, f"{role}_model", "") or self.llm_model
