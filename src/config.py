from __future__ import annotations

import os


class Settings:
    llm_provider: str = os.getenv("LLM_PROVIDER", "mock")
    database_path: str = os.getenv("DATABASE_URL", "capability_library.db")


settings = Settings()
