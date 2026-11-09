"""从 JWT 提取身份 + 读取已有 auth.json 信息"""
import json
import math
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from .token import AUTH_NS, PROFILE_NS, decode_payload


class AuthDataError(ValueError):
    pass


def as_obj(v) -> dict:
    return v if isinstance(v, dict) else {}


def as_str(v) -> str:
    return v if isinstance(v, str) else ""


def iso_utc(dt: datetime) -> str:
    return dt.isoformat(timespec="milliseconds").replace("+00:00", "Z")


def build(session: dict) -> dict:
    payload = decode_payload(session.get("accessToken", ""))
    if payload is None:
        raise AuthDataError("accessToken 不是合法 JWT")

    auth_claim = as_obj(payload.get(AUTH_NS))
    profile_claim = as_obj(payload.get(PROFILE_NS))
    acct = as_obj(session.get("account"))
    usr = as_obj(session.get("user"))

    account_id = (
        as_str(auth_claim.get("chatgpt_account_id"))
        or as_str(session.get("accountId"))
        or as_str(acct.get("id"))
    )
    if not account_id:
        raise AuthDataError("缺少 chatgpt_account_id")

    email = (
        as_str(profile_claim.get("email"))
        or as_str(acct.get("email"))
        or as_str(usr.get("email"))
        or as_str(session.get("email"))
    )

    exp = payload.get("exp") if isinstance(payload.get("exp"), (int, float)) else None
    iat = payload.get("iat") if isinstance(payload.get("iat"), (int, float)) else None
    now = time.time()

    if exp is not None:
        if exp < now:
            raise AuthDataError(
                f"accessToken 已过期 {-int(now - exp)} 秒，请重新登录 ChatGPT"
            )
        if exp < now + 60:
            raise AuthDataError("accessToken 将在 60 秒内过期，请重新登录")

    return {
        "accessToken":   session.get("accessToken", ""),
        "refreshToken":  as_str(session.get("refreshToken")),
        "idToken":       as_str(session.get("idToken")),
        "sessionToken":  as_str(session.get("sessionToken")),
        "accountId":     account_id,
        "chatgptUserId": as_str(auth_claim.get("chatgpt_user_id"))
                          or as_str(auth_claim.get("user_id")),
        "email":         email,
        "name":          email or account_id,
        "planType":      as_str(auth_claim.get("chatgpt_plan_type")),
        "expiresAt":     iso_utc(datetime.fromtimestamp(exp, tz=timezone.utc))
                          if exp else "",
        "expiresIn":     max(0, math.floor(exp - now)) if exp else 0,
        "expiresUnix":   exp,
        "issuedAt":      iso_utc(datetime.fromtimestamp(iat, tz=timezone.utc))
                          if iat else "",
        "lastRefresh":   iso_utc(datetime.fromtimestamp(iat, tz=timezone.utc))
                          if iat else iso_utc(datetime.now(timezone.utc)),
        "generatedAt":   iso_utc(datetime.now(timezone.utc)),
    }


def info_from_auth_json(path: Path) -> Optional[dict]:
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        access = (data.get("tokens") or {}).get("access_token") or ""
        payload = decode_payload(access)
        if not payload:
            return None

        profile = as_obj(payload.get(PROFILE_NS))
        auth = as_obj(payload.get(AUTH_NS))
        exp = payload.get("exp") if isinstance(payload.get("exp"), (int, float)) else None

        return {
            "email":      as_str(profile.get("email")) or "（未知）",
            "plan":       as_str(auth.get("chatgpt_plan_type")) or "未知",
            "account_id": as_str(auth.get("chatgpt_account_id")),
            "exp":        exp,
            "expiresAt":  iso_utc(datetime.fromtimestamp(exp, tz=timezone.utc))
                          if exp else "",
            "expiresIn":  max(0, int(exp - time.time())) if exp else 0,
            "raw":        data,
        }
    except Exception:
        return None