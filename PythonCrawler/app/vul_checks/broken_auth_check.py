from __future__ import annotations
from app.db.database import *
import json
import requests

def response_contains_authenticated_user(body: str) -> bool:
    try:
        data = json.loads(body)
    except Exception:
        return False

    user = data.get("user")

    if user is None:
        return False

    if isinstance(user, dict) and len(user) == 0:
        return False

    return True

#hilfsfunktion um user-Daten auszulesen
def call_whoami(base_url: str, token_value: str | None = None):
    headers = {}

    if token_value:
        headers["Authorization"] = f"Bearer {token_value}"

    try:
        r = requests.get(
            f"{base_url.rstrip('/')}/rest/user/whoami",
            headers=headers,
            timeout=10
        )
        return {
            "status_code": r.status_code,
            "body": r.text,
            "ok": True
        }
    except requests.RequestException as ex:
        return {
            "status_code": None,
            "body": str(ex),
            "ok": False
        }


def test_broken_auth(base_url: str, valid_token: str):
    findings = []

    # 1. gültiger Token
    valid_result = call_whoami(base_url, valid_token)

    if valid_result["status_code"] != 200:
        findings.append({
            "type": "auth_validation_problem",
            "severity": "medium",
            "evidence": f"Gültiger Token liefert keinen erfolgreichen Zugriff: {valid_result['status_code']} | {valid_result['body']}"
        })

    # 2. ohne Token
    no_token_result = call_whoami(base_url)

    if (
        no_token_result["status_code"] == 200 and
        response_contains_authenticated_user(no_token_result["body"])
    ):
        findings.append({
            "type": "broken_authentication",
            "severity": "high",
            "evidence": "Ohne Token wurden authentifizierte Benutzerdaten über /rest/user/whoami zurückgegeben"
        })

    # 3. manipulierten Token testen
    bad_token = valid_token[:-1] + ("X" if valid_token[-1] != "X" else "Y")
    bad_token_result = call_whoami(base_url, bad_token)

    if (
        bad_token_result["status_code"] == 200 and
        response_contains_authenticated_user(bad_token_result["body"])
    ):
        findings.append({
            "type": "broken_authentication",
            "severity": "critical",
            "evidence": "Manipulierter Token wurde akzeptiert und lieferte authentifizierte Benutzerdaten"
        })

    return findings, {
        "valid": valid_result,
        "no_token": no_token_result,
        "bad_token": bad_token_result
    }
