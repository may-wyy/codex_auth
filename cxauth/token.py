"""JWT 解码（只解码 payload，不验签）"""
import base64
import json
from typing import Optional

AUTH_NS = "https://api.openai.com/auth"
PROFILE_NS = "https://api.openai.com/profile"


def decode_payload(token: str) -> Optional[dict]:
    if not isinstance(token, str):
        return None
    parts = token.split(".")
    if len(parts) < 2 or not parts[1]:
        return None
    try:
        padded = parts[1].replace("-", "+").replace("_", "/")
        padded += "=" * (-len(padded) % 4)
        raw = base64.b64decode(padded).decode("utf-8")
        v = json.loads(raw)
        return v if isinstance(v, dict) else None
    except Exception:
        return None


def b64url(text: str) -> str:
    b = base64.b64encode(text.encode("utf-8")).decode("ascii")
    return b.replace("+", "-").replace("/", "_").rstrip("=")