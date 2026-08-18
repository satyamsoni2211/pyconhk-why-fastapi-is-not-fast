from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict

# Anti-pattern 5 (connection pool starvation) is a process-level config, not a
# per-request one — asyncpg pool size is fixed when the engine is created.
# We flip it via POOL_MODE and restart the app process between locust runs.
_POOL_PROFILES = {
    "bad": {
        "pool_size": 5,
        "max_overflow": 10,
        "pool_timeout": 2,
        "pool_recycle": -1,
    },
    "good": {
        "pool_size": 20,
        "max_overflow": 40,
        "pool_timeout": 10,
        "pool_recycle": 1800,
    },
}


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/orders"
    payment_gateway_url: str = "http://localhost:8080"
    pool_mode: Literal["bad", "good"] = "good"

    @property
    def pool_size(self) -> int:
        return _POOL_PROFILES[self.pool_mode]["pool_size"]

    @property
    def max_overflow(self) -> int:
        return _POOL_PROFILES[self.pool_mode]["max_overflow"]

    @property
    def pool_timeout(self) -> int:
        return _POOL_PROFILES[self.pool_mode]["pool_timeout"]

    @property
    def pool_recycle(self) -> int:
        return _POOL_PROFILES[self.pool_mode]["pool_recycle"]


@lru_cache
def get_settings() -> Settings:
    return Settings()
