# ----------------------------
# Form Extraction
# ----------------------------
from __future__ import annotations
from playwright.sync_api import Page
from typing import Any, Dict, List, Optional
from app.db.database import *

#Forms der pageURL extrahieren
def extract_forms(page: Page) -> List[Dict[str, Any]]:

    results: List[Dict[str, Any]] = []

    results.extend(extract_html_forms(page))

    if not results:
        results.extend(extract_spa_form_candidates(page))

    return results

#html forms gesucht
def extract_html_forms(page: Page) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []

    for form in page.locator("form").all():
        inputs = []
        for inp in form.locator("input, textarea, select").all():
            inputs.append(describe_field(inp))

        out.append({
            "type": "html_form",
            "url": page.url,
            "action": form.get_attribute("action"),
            "method": (form.get_attribute("method") or "GET").upper(),
            "inputs": inputs,
        })

    return out

#spa forms
def extract_spa_form_candidates(page: Page) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []

    #releveante Eingabefelder
    field_locator = page.locator("input:not([type=hidden]), textarea, select")
    fields = field_locator.all()

    if not fields:
        return out

    containers: Dict[str, List[Any]] = {}

    for f in fields:
        if not f.is_visible():
            continue

        #javascript um das nächste umgebende Element zu suchen was zu sinnvoller Liste von Containern gehört
        container_sel = f.evaluate(
            """(el) => {
                const c =
                  el.closest('mat-card, .mat-mdc-card, mat-dialog-container, .cdk-overlay-pane, section, main, article, body');
                if (!c) return 'body';
                // versuche etwas Stabileres zu bauen:
                if (c.id) return `#${c.id}`;
                // sonst: tagname + erste class
                const cls = (c.classList && c.classList.length) ? '.' + c.classList[0] : '';
                return c.tagName.toLowerCase() + cls;
            }"""
        )
        containers.setdefault(container_sel, []).append(f)

    #containers auswerten
    for container_sel, container_fields in containers.items():
        #locator für den container holen
        container = page.locator(container_sel).first if container_sel != "body" else page.locator("body")

        #passenden submitbutton finden
        submit_btn = find_submit_button(container)
        #alle Felder beschreiben
        inputs_desc = [describe_field(f) for f in container_fields]
        #Zweck herausfinden
        intent = infer_intent(inputs_desc, submit_btn_text=(submit_btn.inner_text().strip() if submit_btn else ""))

        out.append({
            "type": "spa_form_candidate",
            "url": page.url,
            "container": container_sel,
            "intent": intent,
            "submit": {
                "text": submit_btn.inner_text().strip(),
                "selector_hint": safe_selector_hint(submit_btn),
            } if submit_btn else None,
            "inputs": inputs_desc,
        })

    #login Formulare werden als erstes angezeigt
    out.sort(key=lambda x: 0 if x.get("intent") == "login" else 1)
    return out

#generalisiert submitButton finden
def find_submit_button(container_locator) -> Optional[Any]:
    candidates = container_locator.locator(
        "button, input[type=submit], [role=button], a[role=button]"
    ).all()

    best = None
    best_score = -1

    keywords = ["log in", "login", "sign in", "submit", "search", "send", "continue", "next", "anmelden"]
    for c in candidates:
        if not c.is_visible():
            continue
        text = (c.inner_text() or "").strip().lower()
        aria = (c.get_attribute("aria-label") or "").strip().lower()
        typ = (c.get_attribute("type") or "").strip().lower()

        score = 0
        if typ == "submit":
            score += 3
        for k in keywords:
            if k in text or k in aria:
                score += 5

        if c.get_attribute("disabled") is not None:
            score -= 10

        #den button mit höchster Wahrscheinlichkeit finden
        if score > best_score:
            best = c
            best_score = score

    return best


#intent des Formulars finden
def infer_intent(inputs_desc: List[Dict[str, Any]], submit_btn_text: str) -> str:
    text = (submit_btn_text or "").lower()
    names = " ".join([(i.get("name") or "") + " " + (i.get("placeholder") or "") + " " + (i.get("label") or "")
                      for i in inputs_desc]).lower()

    if "password" in names and ("email" in names or "user" in names or "username" in names):
        return "login"
    if "search" in names or "search" in text:
        return "search"
    if "register" in names or "sign up" in names:
        return "register"
    return "unknown"

#strukturiertes Beschreiben von Eingabefeld
def describe_field(field_locator) -> Dict[str, Any]:
    name = field_locator.get_attribute("name")
    fid = field_locator.get_attribute("id")
    ftype = field_locator.get_attribute("type") or field_locator.evaluate("(el) => el.tagName.toLowerCase()")
    placeholder = field_locator.get_attribute("placeholder")

    #mit javaScript label herausfinden
    label = field_locator.evaluate(
        """(el) => {
            const id = el.getAttribute('id');
            if (id) {
                const l = document.querySelector(`label[for="${id}"]`);
                if (l) return l.innerText;
            }
            // Angular Material: mat-label in der Nähe
            const matLabel = el.closest('mat-form-field, .mat-mdc-form-field')?.querySelector('mat-label');
            if (matLabel) return matLabel.textContent;
            // aria-label fallback
            return el.getAttribute('aria-label') || '';
        }"""
    )

    return {
        "name": name,
        "id": fid,
        "type": ftype,
        "placeholder": placeholder,
        "label": (label or "").strip(),
    }

#id bzw tagname herausfinden
def safe_selector_hint(locator) -> str:
    try:
        return locator.evaluate(
            """(el) => {
                if (el.id) return `#${el.id}`;
                const cls = el.classList && el.classList.length ? '.' + el.classList[0] : '';
                return el.tagName.toLowerCase() + cls;
            }"""
        )
    except Exception:
        return ""


