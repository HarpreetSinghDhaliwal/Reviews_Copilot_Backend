from pydantic import BaseSettings, Field, SecretStr, validator
from pathlib import Path
from typing import Optional

class Settings(BaseSettings):
    # --- Core Application Settings ---
    APP_NAME: str = Field(default="ReviewsCopilot", alias="app_name")
    ENV: str = Field(alias="app_env")
    APP_PORT: int = Field(default=8000, alias="app_port")
    DATABASE_URL: str = Field(alias="database_url")
    API_KEY: SecretStr = Field(alias="api_key")

    # --- AI Service Settings ---
    OPENAI_API_KEY: Optional[SecretStr] = Field(default=None, alias="openai_api_key")
    GEMINI_API_KEY: Optional[str] = Field(default=None, alias="gemini_api_key")
    GEMINI_PROJECT_ID: Optional[str] = Field(default=None, alias="gemini_project_id")
    GEMINI_MODEL_ID: Optional[str] = Field(default=None, alias="gemini_model_id")
    
    # --- HuggingFace Local Pipeline Settings ---
    HF_MODEL_SENTIMENT: str = Field(
        default="distilbert-base-uncased-finetuned-sst-2-english",
        alias="hf_model_sentiment"
    )
    HF_MODEL_SUMMARIZATION: str = Field(
        default="sshleifer/distilbart-cnn-12-6",
        alias="hf_model_summarization"
    )

    # --- Utility Settings ---
    TFIDF_DIR: Path = Path("./data/tfidf")
    REDACT_PHONE: bool = True
    REDACT_EMAIL: bool = True
    LOG_LEVEL: str = "INFO"

    # Validator to ensure TFIDF_DIR exists
    @validator("TFIDF_DIR", pre=True)
    def ensure_path(cls, v):
        p = Path(v) if isinstance(v, str) else v
        p.mkdir(parents=True, exist_ok=True)
        return p

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"
        allow_population_by_field_name = True

settings = Settings()
