import os
import sys
import pytest

@pytest.fixture(autouse=True, scope="session")
def add_project_root_to_sys_path():
    """Ensure the project root is available on sys.path for imports."""
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
    yield
    # No cleanup required; keep path for duration of session
