from __future__ import annotations
from app.db.database import *
from playwright.sync_api import Page, TimeoutError as PWTimeoutError


#-----------------------------
#closing overlays / popups
#-------------------------------

def dismiss_overlays(page: Page) -> None:
    try:
        overlay = page.locator(".cdk-overlay-container .mat-mdc-dialog-surface")
        if overlay.count() > 0 and overlay.first.is_visible():
            page.keyboard.press("Escape")
            page.wait_for_timeout(200)
    except Exception:
        pass

    candidates = [
        ".cdk-overlay-container button:has-text('Close')",
        ".cdk-overlay-container button:has-text('Dismiss')",
        ".cdk-overlay-container button:has-text('OK')",
        ".cdk-overlay-container button:has-text('Got it')",
        ".cdk-overlay-container button[aria-label='Close']",
        ".cdk-overlay-container [mat-dialog-close]",
    ]
    for sel in candidates:
        btn = page.locator(sel).first
        try:
            if btn.count() > 0 and btn.is_visible():
                btn.click(timeout=1000)
                page.wait_for_timeout(200)
                break
        except Exception:
            pass

def dismiss_popups(page: Page) -> None:
    try:
        page.get_by_role("button", name="Dismiss").click(timeout=1200)
    except PWTimeoutError:
        pass

    try:
        page.get_by_role("button", name="Me want it!").click(timeout=1200)
    except PWTimeoutError:
        pass
    try:
        page.keyboard.press("Escape")
    except Exception:
        pass


