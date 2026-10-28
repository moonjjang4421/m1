from functools import lru_cache

from backend.config import get_settings
from backend.database import Repository, build_repository


@lru_cache
def get_repository() -> Repository:
    return build_repository(get_settings())

