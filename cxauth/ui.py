"""ANSI 颜色 + 分隔线 + 提示样式"""
import os
import sys


class Color:
    ENABLED = True
    _RESET = "\033[0m"
    GREEN = "\033[32m"
    RED = "\033[31m"
    YELLOW = "\033[33m"
    CYAN = "\033[36m"
    GRAY = "\033[90m"

    @classmethod
    def disable(cls) -> None:
        cls.ENABLED = False

    @classmethod
    def wrap(cls, text: str, color: str) -> str:
        if not cls.ENABLED:
            return text
        return f"{color}{text}{cls._RESET}"


def _supports_color() -> bool:
    if os.environ.get("NO_COLOR"):
        return False
    if not sys.stdout.isatty():
        return False
    if sys.platform == "win32":
        try:
            import ctypes
            kernel32 = ctypes.windll.kernel32
            kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
            return True
        except Exception:
            return False
    return True


def init() -> None:
    if not _supports_color():
        Color.disable()


def ok(text: str) -> str:
    return Color.wrap(f"✓ {text}", Color.GREEN)


def err(text: str) -> str:
    return Color.wrap(f"✗ {text}", Color.RED)


def warn(text: str) -> str:
    return Color.wrap(f"⚠ {text}", Color.YELLOW)


def info(text: str) -> str:
    return Color.wrap(f"ℹ {text}", Color.CYAN)


def dim(text: str) -> str:
    return Color.wrap(text, Color.GRAY)


def divider(char: str = "━", width: int = 50) -> str:
    return dim(char * width)