"""session 解析：支持三种粘贴格式"""
import json
from typing import Optional

from .token import decode_payload


def parse(raw: str) -> Optional[dict]:
    text = (raw or "").strip()
    if not text:
        return None

    try:
        obj = json.loads(text)
    except Exception:
        obj = None

    if isinstance(obj, dict) and obj.get("accessToken"):
        return obj

    if isinstance(obj, dict) and isinstance(obj.get("access_token"), str):
        return {
            "accessToken":  obj.get("access_token"),
            "refreshToken": obj.get("refresh_token"),
            "idToken":      obj.get("id_token"),
            "sessionToken": obj.get("session_token"),
            "accountId":    obj.get("account_id"),
            "account":      obj.get("account"),
            "user":         obj.get("user"),
            "email":        obj.get("email"),
        }

    if decode_payload(text):
        return {"accessToken": text}

    return None