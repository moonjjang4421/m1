import os

os.environ["USE_MEMORY_DB"] = "true"
os.environ["OPENAI_API_KEY"] = "test-key"

import pytest
from fastapi.testclient import TestClient

from backend.dependencies import get_repository
from backend.main import app


@pytest.fixture(autouse=True)
def clean_repository():
    get_repository.cache_clear()
    yield
    get_repository.cache_clear()


@pytest.fixture
def client():
    return TestClient(app)

