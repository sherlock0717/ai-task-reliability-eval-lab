"""Load settings from environment and optional `.env` in repo root."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


def _load_dotenv(repo_root: Path) -> None:
    env_path = repo_root / ".env"
    if not env_path.is_file():
        return
    try:
        from dotenv import load_dotenv  # type: ignore
    except ImportError:
        # Minimal parser: KEY=VALUE lines, no export keyword
        for line in env_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" not in line:
                continue
            k, _, v = line.partition("=")
            k, v = k.strip(), v.strip().strip('"').strip("'")
            if k and k not in os.environ:
                os.environ[k] = v
        return
    load_dotenv(env_path)


def _truthy(val: Optional[str]) -> bool:
    if val is None:
        return False
    return val.strip().lower() in ("1", "true", "yes", "on")


@dataclass(frozen=True)
class Settings:
    """LLM-related settings; safe defaults for offline mock runs."""

    use_real_llm: bool
    openai_compat_base_url: str
    openai_compat_api_key: str
    openai_compat_model: str

    @property
    def real_llm_ready(self) -> bool:
        return bool(
            self.use_real_llm
            and self.openai_compat_base_url.strip()
            and self.openai_compat_api_key.strip()
            and self.openai_compat_model.strip()
        )


def load_settings(repo_root: Optional[Path] = None) -> Settings:
    root = Path(repo_root) if repo_root else Path.cwd()
    _load_dotenv(root)
    return Settings(
        use_real_llm=_truthy(os.environ.get("USE_REAL_LLM")),
        openai_compat_base_url=os.environ.get("OPENAI_COMPAT_BASE_URL", "").strip(),
        openai_compat_api_key=os.environ.get("OPENAI_COMPAT_API_KEY", "").strip(),
        openai_compat_model=os.environ.get("OPENAI_COMPAT_MODEL", "").strip(),
    )
