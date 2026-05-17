import requests

#response = requests.get('http://localhost:3000')

# Alle Header auslesen
#print(response.headers)
#print(response.headers['Content-Type'])
#print(response.headers.get('content-type'))

def analyze_security_headers(headers: dict, url: str):
    findings = []

    # case insensetive
    normalized = {k.lower(): v for k, v in headers.items()}
    is_https = url.lower().startswith("https://")

    # Content-Security-Policy
    csp = normalized.get("content-security-policy")
    if not csp:
        findings.append({
            "type": "missing_security_header",
            "severity": "high",
            "header": "Content-Security-Policy",
            "evidence": "Header fehlt"
        })
    else:
        if "unsafe-inline" in csp or "unsafe-eval" in csp:
            findings.append({
                "type": "weak_security_header",
                "severity": "medium",
                "header": "Content-Security-Policy",
                "evidence": f"Unsichere Direktiven gefunden: {csp}"
            })

    # X-Frame-Options
    xfo = normalized.get("x-frame-options")
    if not xfo:
        findings.append({
            "type": "missing_security_header",
            "severity": "medium",
            "header": "X-Frame-Options",
            "evidence": "Header fehlt"
        })
    elif xfo.upper() not in ["DENY", "SAMEORIGIN"]:
        findings.append({
            "type": "weak_security_header",
            "severity": "medium",
            "header": "X-Frame-Options",
            "evidence": f"Unerwarteter Wert: {xfo}"
        })

    # X-Content-Type-Options
    xcto = normalized.get("x-content-type-options")
    if not xcto:
        findings.append({
            "type": "missing_security_header",
            "severity": "medium",
            "header": "X-Content-Type-Options",
            "evidence": "Header fehlt"
        })
    elif xcto.lower() != "nosniff":
        findings.append({
            "type": "weak_security_header",
            "severity": "medium",
            "header": "X-Content-Type-Options",
            "evidence": f"Unerwarteter Wert: {xcto}"
        })

    # Strict-Transport-Security
    hsts = normalized.get("strict-transport-security")
    if is_https:
        if not hsts:
            findings.append({
                "type": "missing_security_header",
                "severity": "high",
                "header": "Strict-Transport-Security",
                "evidence": "HTTPS-Seite ohne HSTS"
            })
        else:
            if "max-age=" not in hsts.lower():
                findings.append({
                    "type": "weak_security_header",
                    "severity": "medium",
                    "header": "Strict-Transport-Security",
                    "evidence": f"Kein max-age gefunden: {hsts}"
                })

    # Referrer-Policy
    referrer = normalized.get("referrer-policy")
    if not referrer:
        findings.append({
            "type": "missing_security_header",
            "severity": "low",
            "header": "Referrer-Policy",
            "evidence": "Header fehlt"
        })

    # Permissions-Policy
    permissions = normalized.get("permissions-policy")
    feature_policy = normalized.get("feature-policy")

    if not permissions:
        findings.append({
            "type": "missing_security_header",
            "severity": "low",
            "header": "Permissions-Policy",
            "evidence": "Header fehlt"
        })

    if feature_policy and not permissions:
        findings.append({
            "type": "deprecated_header",
            "severity": "low",
            "header": "Feature-Policy",
            "evidence": f"Veralteter Header gefunden: {feature_policy}"
        })

    # CORS
    acao = normalized.get("access-control-allow-origin")
    if acao == "*":
        findings.append({
            "type": "cors_misconfiguration_possible",
            "severity": "medium",
            "header": "Access-Control-Allow-Origin",
            "evidence": "Wert ist '*'"
        })

    return findings
