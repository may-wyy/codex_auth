"""跨平台剪贴板读取"""
import shutil
import subprocess
import sys


def read() -> str:
    try:
        if sys.platform == "darwin":
            r = subprocess.run(["pbpaste"], capture_output=True, text=True, timeout=3)
            return r.stdout if r.returncode == 0 else ""

        if sys.platform == "win32":
            r = subprocess.run(
                ["powershell", "-NoProfile", "-command", "Get-Clipboard"],
                capture_output=True, text=True, timeout=5,
            )
            return r.stdout if r.returncode == 0 else ""

        for cmd in (
            ["xclip", "-selection", "clipboard", "-o"],
            ["wl-paste", "--no-newline"],
            ["xsel", "--clipboard", "--output"],
        ):
            try:
                r = subprocess.run(cmd, capture_output=True, text=True, timeout=3)
                if r.returncode == 0 and r.stdout:
                    return r.stdout
            except (FileNotFoundError, subprocess.TimeoutExpired):
                continue
        return ""
    except Exception:
        return ""


def available() -> bool:
    if sys.platform == "darwin":
        return shutil.which("pbpaste") is not None
    if sys.platform == "win32":
        return True
    return any(shutil.which(cmd) for cmd in ("xclip", "wl-paste", "xsel"))