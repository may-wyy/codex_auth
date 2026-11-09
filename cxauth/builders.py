"""各平台输出生成器"""
import base64
import json
import re
import time

from .token import AUTH_NS, b64url


def auth_json(data: dict) -> str:
    return json.dumps({
        "auth_mode":      "chatgpt",
        "OPENAI_API_KEY": None,
        "tokens": {
            "id_token":      data["accessToken"],
            "access_token":  data["accessToken"],
            "refresh_token": data.get("refreshToken") or "rt_mock_token",
            "account_id":    data["accountId"],
        },
        "last_refresh": data["lastRefresh"],
    }, indent=2, ensure_ascii=False) + "\n"


def synthetic_jwt(data: dict) -> str:
    header = b64url(json.dumps(
        {"alg": "none", "typ": "JWT", "cpa_synthetic": True},
        separators=(",", ":"),
    ))
    payload = {
        "iat": int(time.time()),
        AUTH_NS: {
            "chatgpt_account_id": data["accountId"],
            "chatgpt_plan_type":  data["planType"],
            "chatgpt_user_id":    data["chatgptUserId"],
            "user_id":            data["chatgptUserId"],
        },
        "email": data["email"],
    }
    if data.get("expiresUnix") is not None:
        payload["exp"] = data["expiresUnix"]
    payload_str = b64url(json.dumps(payload, separators=(",", ":"), ensure_ascii=False))
    return f"{header}.{payload_str}."


def unix_script(auth_json_str: str) -> str:
    return "\n".join([
        "mkdir -p ~/.codex",
        "cat > ~/.codex/auth.json <<'CODEX_AUTH_JSON'",
        auth_json_str.rstrip(),
        "CODEX_AUTH_JSON",
        "chmod 600 ~/.codex/auth.json",
    ])


def windows_script(auth_json_str: str) -> str:
    b64 = base64.b64encode(auth_json_str.encode("utf-8")).decode("ascii")
    chunks = re.findall(r".{1,76}", b64) or []
    return "\r\n".join([
        "@echo off",
        'if not exist "%USERPROFILE%\\.codex" mkdir "%USERPROFILE%\\.codex"',
        '> "%TEMP%\\codex_auth.b64" (',
        *[f"  echo {c}" for c in chunks],
        ")",
        'certutil -f -decode "%TEMP%\\codex_auth.b64" "%USERPROFILE%\\.codex\\auth.json" >nul',
        'del "%TEMP%\\codex_auth.b64"',
    ]) + "\r\n"


def _email_key(email: str) -> str:
    return re.sub(r"[^a-zA-Z0-9]+", "_", email).strip("_")


def cpa(data: dict) -> str:
    id_token = data["idToken"] or synthetic_jwt(data)
    return json.dumps({
        "type": "codex",
        "account_id": data["accountId"],
        "chatgpt_account_id": data["accountId"],
        "email": data["email"],
        "name": data["name"],
        "plan_type": data["planType"],
        "chatgpt_plan_type": data["planType"],
        "id_token": id_token,
        "id_token_synthetic": not data["idToken"],
        "access_token": data["accessToken"],
        "session_token": data["sessionToken"],
        "last_refresh": data["lastRefresh"],
        "expired": data["expiresAt"],
    }, indent=2, ensure_ascii=False)


def sub2api(data: dict) -> str:
    return json.dumps({
        "exported_at": data["lastRefresh"],
        "proxies": [],
        "accounts": [{
            "name": data["name"],
            "platform": "openai",
            "type": "oauth",
            "concurrency": 10,
            "priority": 1,
            "credentials": {
                "access_token": data["accessToken"],
                "chatgpt_account_id": data["accountId"],
                "chatgpt_user_id": data["chatgptUserId"],
                "email": data["email"],
                "expires_at": data["expiresAt"],
                "expires_in": data["expiresIn"],
                "plan_type": data["planType"],
            },
            "extra": {
                "email": data["email"],
                "email_key": _email_key(data["email"]),
                "name": data["name"],
                "auth_provider": "openai",
                "source": "chatgpt_web_session",
                "last_refresh": data["lastRefresh"],
            },
        }],
    }, indent=2, ensure_ascii=False)


def cockpit(data: dict) -> str:
    return json.dumps({
        "type": "codex",
        "id_token": data["idToken"] or synthetic_jwt(data),
        "access_token": data["accessToken"],
        "refresh_token": data["refreshToken"],
        "account_id": data["accountId"],
        "last_refresh": data["lastRefresh"],
        "email": data["email"],
        "expired": data["expiresAt"],
    }, indent=2, ensure_ascii=False)