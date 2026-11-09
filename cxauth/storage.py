"""写入 + 备份策略 + 恢复"""
import os
import shutil
from pathlib import Path
from typing import Optional

from .paths import codex_home_dir


class StorageError(Exception):
    pass


def write_auth(auth_json_str: str,
               codex_home: Optional[Path] = None,
               reset_backup: bool = False) -> dict:
    codex_dir = codex_home or codex_home_dir()
    try:
        codex_dir.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        raise StorageError(f"无法创建 {codex_dir}: {e}")

    auth_file = codex_dir / "auth.json"
    bak_file = codex_dir / "auth.json.bak"

    backup_created = False
    backup_existed = bak_file.exists()
    backup_updated = False

    try:
        if reset_backup and auth_file.exists():
            shutil.copy2(auth_file, bak_file)
            backup_updated = True
        elif auth_file.exists() and not bak_file.exists():
            shutil.copy2(auth_file, bak_file)
            backup_created = True

        tmp = codex_dir / ".auth.json.tmp"
        tmp.write_text(auth_json_str, encoding="utf-8")
        if os.name == "posix":
            os.chmod(tmp, 0o600)
        tmp.replace(auth_file)
    except OSError as e:
        raise StorageError(f"写入失败: {e}")

    return {
        "auth_file": auth_file,
        "backup_created": backup_created,
        "backup_existed": backup_existed,
        "backup_updated": backup_updated,
    }


def restore(codex_home: Optional[Path] = None,
            save_current: bool = True) -> dict:
    codex_dir = codex_home or codex_home_dir()
    auth_file = codex_dir / "auth.json"
    bak_file = codex_dir / "auth.json.bak"
    before = codex_dir / "auth.json.before-restore"

    if not bak_file.exists():
        raise StorageError(f"未找到原始配置备份: {bak_file}")

    saved = None
    if save_current and auth_file.exists():
        shutil.copy2(auth_file, before)
        saved = before

    shutil.copy2(bak_file, auth_file)
    if os.name == "posix":
        os.chmod(auth_file, 0o600)

    return {
        "auth_file": auth_file,
        "bak_file": bak_file,
        "before_restore": saved,
    }


def inspect(codex_home: Optional[Path] = None) -> dict:
    codex_dir = codex_home or codex_home_dir()
    auth_file = codex_dir / "auth.json"
    bak_file = codex_dir / "auth.json.bak"
    return {
        "codex_dir": codex_dir,
        "auth_file": auth_file,
        "bak_file": bak_file,
        "auth_exists": auth_file.exists(),
        "bak_exists": bak_file.exists(),
    }