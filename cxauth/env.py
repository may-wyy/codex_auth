"""环境检查"""
import shutil
import socket
import sys
from pathlib import Path
from typing import List, Tuple

from . import clipboard
from .paths import codex_home_dir


class Check:
    def __init__(self, level: str, name: str, ok: bool,
                 message: str = "", hint: str = ""):
        self.level = level
        self.name = name
        self.ok = ok
        self.message = message
        self.hint = hint


def _check_python() -> Check:
    v = sys.version_info
    ok = v >= (3, 7)
    return Check("info" if ok else "fatal", "Python 版本", ok,
                 f"{v.major}.{v.minor}.{v.micro}",
                 "需要 Python 3.7+" if not ok else "")


def _check_system() -> Check:
    import platform
    os_name = {"darwin": "macOS", "win32": "Windows",
               "linux": "Linux"}.get(sys.platform, sys.platform)
    return Check("info", "操作系统", True, f"{os_name} {platform.release()}")


def _check_codex_dir() -> Check:
    codex_dir = codex_home_dir()
    try:
        codex_dir.mkdir(parents=True, exist_ok=True)
        probe = codex_dir / ".write_probe"
        probe.write_text("")
        probe.unlink()
        return Check("info", f"{codex_dir} 可写", True)
    except OSError as e:
        return Check("fatal", f"{codex_dir} 可写", False, str(e),
                     f"mkdir -p {codex_dir} && chmod 700 {codex_dir}")


def _check_disk(threshold_mb: int = 10) -> Check:
    try:
        _, _, free = shutil.disk_usage(Path.home())
        free_mb = free // (1024 * 1024)
        ok = free_mb >= threshold_mb
        return Check("info" if ok else "warn", "磁盘空间", ok,
                     f"可用 {free_mb} MB")
    except Exception:
        return Check("info", "磁盘空间", True, "无法检测")


def _check_clipboard() -> Check:
    if clipboard.available():
        return Check("info", "剪贴板工具", True)
    return Check("warn", "剪贴板工具", False,
                 "未找到可用的剪贴板命令",
                 "将降级为手动粘贴")


def _check_network(timeout: float = 2.0) -> Check:
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(timeout)
        s.connect(("chatgpt.com", 443))
        s.close()
        return Check("info", "网络可达 chatgpt.com", True)
    except Exception:
        return Check("warn", "网络可达 chatgpt.com", False,
                     "无法连接", "浏览器仍可能正常访问")


def run_all() -> Tuple[List[Check], bool]:
    checks = [
        _check_python(),
        _check_system(),
        _check_clipboard(),
        _check_codex_dir(),
        _check_disk(),
        _check_network(),
    ]
    has_fatal = any(c.level == "fatal" and not c.ok for c in checks)
    return checks, has_fatal