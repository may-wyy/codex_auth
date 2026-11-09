"""路径解析：~/.codex、codex-output/"""
import os
from pathlib import Path
from typing import Optional

OUTPUT_DIR_NAME = "codex-output"


def codex_home_dir() -> Path:
    """~/.codex 或 $CODEX_HOME"""
    env = os.environ.get("CODEX_HOME")
    return Path(env).expanduser() if env else Path.home() / ".codex"


def output_dir(override: Optional[str] = None,
               script_dir: Optional[Path] = None) -> Path:
    """生成物目录：默认工程根下的 codex-output/，不可写则退化到 ~/codex-output/"""
    if override:
        d = Path(override).expanduser().resolve()
        d.mkdir(parents=True, exist_ok=True)
        return d

    base = Path(script_dir) if script_dir else Path(__file__).resolve().parent.parent
    d = base / OUTPUT_DIR_NAME

    try:
        d.mkdir(parents=True, exist_ok=True)
        probe = d / ".write_probe"
        probe.write_text("")
        probe.unlink()
        return d
    except (PermissionError, OSError):
        d = Path.home() / OUTPUT_DIR_NAME
        d.mkdir(parents=True, exist_ok=True)
        return d


def ensure_gitignore(out_dir: Path) -> None:
    gi = out_dir / ".gitignore"
    if not gi.exists():
        gi.write_text("*\n", encoding="utf-8")