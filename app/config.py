from functools import lru_cache
from pathlib import Path
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    auth_enabled: bool = True
    # Stringa CSV: "key1,key2,key3" — gestita come property
    api_keys: str = Field(default="")
    rate_limit: str = "60/minute"
    sample_files_dir: Path = Path("sample_files")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )

    def get_api_keys(self) -> list[str]:
        return [k.strip() for k in self.api_keys.split(",") if k.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
