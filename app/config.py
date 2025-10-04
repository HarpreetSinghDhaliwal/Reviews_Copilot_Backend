from pydantic_settings import BaseSettings
from pydantic import Field, SecretStr, field_validator
from pathlib import Path
from typing import Optional

class Settings(BaseSettings):
    APP_NAME: str = Field(default="ReviewsCopilot", alias="app_name")
    ENV: str = Field(alias="app_env")
    APP_PORT: int = Field(default=8000, alias="app_port")
    DATABASE_URL: str = Field(alias="database_url")
    API_KEY: SecretStr = Field(alias="api_key")

    OPENAI_API_KEY: Optional[SecretStr] = Field(default=None, alias="openai_api_key")
    GEMINI_API_KEY: Optional[str] = Field(default=None, alias="gemini_api_key")
    GEMINI_PROJECT_ID: Optional[str] = Field(default=None, alias="gemini_project_id")
    GEMINI_MODEL_ID: Optional[str] = Field(default=None, alias="gemini_model_id")
    
    HF_MODEL_SENTIMENT: str = Field(
        default="distilbert-base-uncased-finetuned-sst-2-english",
        alias="hf_model_sentiment"
    )
    HF_MODEL_SUMMARIZATION: str = Field(
        default="sshleifer/distilbart-cnn-12-6",
        alias="hf_model_summarization"
    )

    TFIDF_DIR: Path = Path("./data/tfidf")
    REDACT_PHONE: bool = True
    REDACT_EMAIL: bool = True
    LOG_LEVEL: str = "INFO"

    # Pydantic v2 field_validator
    @field_validator("TFIDF_DIR")
    def ensure_path(cls, v: Path) -> Path:
        if isinstance(v, str):
            v = Path(v)
        v.mkdir(parents=True, exist_ok=True)
        return v

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"
        populate_by_name = True  # Pydantic v2 replacement for allow_population_by_field_name

settings = Settings()
