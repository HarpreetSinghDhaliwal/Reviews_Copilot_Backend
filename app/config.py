from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, SecretStr, field_validator
from pathlib import Path

class Settings(BaseSettings):
    # --- Core Application Settings (Explicitly aliased to match common lowercase environment variables) ---
    APP_NAME: str = Field(default="ReviewsCopilot", alias="app_name")
    ENV: str = Field(alias="app_env")
    APP_PORT: int = Field(default=8000, alias="app_port")
    DATABASE_URL: str = Field(alias="database_url")
    API_KEY: SecretStr = Field(alias="api_key")

    # --- AI Service Settings (Explicitly aliased) ---
    OPENAI_API_KEY: SecretStr | None = Field(default=None, alias="openai_api_key")
    GEMINI_API_KEY: str | None = Field(default=None, alias="gemini_api_key")
    GEMINI_PROJECT_ID: str | None = Field(default=None, alias="gemini_project_id")
    GEMINI_MODEL_ID: str | None = Field(default=None, alias="gemini_model_id")
    
    # --- HuggingFace (HF) Local Pipeline Settings (Explicitly aliased to resolve 'Extra inputs') ---
    HF_MODEL_SENTIMENT: str = Field(
        default="distilbert-base-uncased-finetuned-sst-2-english",
        alias="hf_model_sentiment"
    )
    HF_MODEL_SUMMARIZATION: str = Field(
        default="sshleifer/distilbart-cnn-12-6",
        alias="hf_model_summarization"
    )

    # --- Utility Settings (No change, as these were not reported in errors) ---
    TFIDF_DIR: Path = Path("./data/tfidf")
    REDACT_PHONE: bool = True
    REDACT_EMAIL: bool = True
    LOG_LEVEL: str = "INFO"

    # Pydantic V2 configuration for settings
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra='ignore' ,
        populate_by_name=True 
    )

    # Validator updated for Pydantic V2 (field_validator)
    @field_validator("TFIDF_DIR", mode='before')
    @classmethod
    def ensure_path(cls, v):
        # This function ensures the path exists before Pydantic validates it as a Path object
        p = Path(v) if isinstance(v, str) else v
        p.mkdir(parents=True, exist_ok=True)
        return p

settings = Settings()
