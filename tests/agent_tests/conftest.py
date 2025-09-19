import pytest
from agent.config import Settings

@pytest.fixture(scope="session")
def settings():
    return Settings()
