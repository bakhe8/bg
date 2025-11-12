"""
Path registry for the refactored BGLApp layout.

This module mirrors the legacy ``main.config`` paths so that both the
current system and the refactor prototype share the exact same sources
for data/logs/templates during the migration window.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path
import os

from main import config as legacy_config


@dataclass(frozen=True, slots=True)
class PathRegistry:
    root_dir: Path
    web_dir: Path
    templates_dir: Path
    assets_dir: Path
    data_dir: Path
    archives_dir: Path
    exports_dir: Path
    logs_dir: Path
    review_dir: Path
    reference_dir: Path


LEGACY_PATHS = PathRegistry(
    root_dir=legacy_config.ROOT_DIR,
    web_dir=legacy_config.WEB_DIR,
    templates_dir=legacy_config.TEMPLATES_DIR,
    assets_dir=legacy_config.ASSETS_DIR,
    data_dir=legacy_config.DATA_DIR,
    archives_dir=legacy_config.ARCHIVES_DIR,
    exports_dir=legacy_config.EXPORTS_DIR,
    logs_dir=legacy_config.LOGS_DIR,
    review_dir=legacy_config.REVIEW_DIR,
    reference_dir=legacy_config.REFERENCE_DIR,
)


# The refactor workspace root (…/BGLApp_Refactor)
REFACTOR_ROOT = Path(__file__).resolve().parents[2]
REFACTOR_WEB_DIR = REFACTOR_ROOT / "web"
REFACTOR_TEMPLATES_DIR = REFACTOR_WEB_DIR / "templates"
REFACTOR_ASSETS_DIR = REFACTOR_WEB_DIR / "assets"


class EnvironmentConfig:
    """Convenience wrapper for switching between refactor/legacy paths."""

    def __init__(self, env: str | None = None):
        self.env = (env or os.getenv("BGLAPP_ENV", "development")).lower()

    def _use_refactor(self) -> bool:
        return self.env not in {"production", "legacy"}

    @property
    def web_dir(self) -> Path:
        return REFACTOR_WEB_DIR if self._use_refactor() else LEGACY_PATHS.web_dir

    @property
    def templates_dir(self) -> Path:
        return REFACTOR_TEMPLATES_DIR if self._use_refactor() else LEGACY_PATHS.templates_dir

    @property
    def assets_dir(self) -> Path:
        base = REFACTOR_ASSETS_DIR if self._use_refactor() else LEGACY_PATHS.assets_dir
        return base

    @property
    def data_dir(self) -> Path:
        return LEGACY_PATHS.data_dir

    def asdict(self):
        return {
            "env": self.env,
            "web_dir": str(self.web_dir),
            "templates_dir": str(self.templates_dir),
            "assets_dir": str(self.assets_dir),
            "data_dir": str(self.data_dir),
        }


DEFAULT_CONFIG = EnvironmentConfig()


__all__ = [
    "PathRegistry",
    "LEGACY_PATHS",
    "REFACTOR_ROOT",
    "REFACTOR_WEB_DIR",
    "REFACTOR_TEMPLATES_DIR",
    "REFACTOR_ASSETS_DIR",
    "EnvironmentConfig",
    "DEFAULT_CONFIG",
]
