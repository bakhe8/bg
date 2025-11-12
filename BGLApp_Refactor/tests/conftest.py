from __future__ import annotations

import sys
from pathlib import Path
from typing import Iterator

import pytest


@pytest.fixture(scope="session")
def project_root() -> Path:
    return Path(__file__).resolve().parents[2]


@pytest.fixture(scope="session", autouse=True)
def _set_sys_path(project_root: Path) -> Iterator[None]:
    """Ensure ``import BGLApp_Refactor`` works when tests run from anywhere."""
    added = False
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
        added = True
    try:
        yield
    finally:
        if added:
            sys.path.remove(str(project_root))
