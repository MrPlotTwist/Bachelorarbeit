#--------------------
#-      XSS testing
#--------------------------
#testingphrase: <iframe src="javascript:alert(`xss`)">
from __future__ import annotations
from playwright.sync_api import Page, TimeoutError as PWTimeoutError
from app.db.database import *

#Juice Shop spezifisch
def xss_validation(page: Page) -> bool:
    page.get_by_text("search").click()
    inp = page.locator("#mat-input-1")
    inp.click()
    inp.fill('<iframe src="javascript:alert(`xss`)">')

    try:
        with page.expect_event("dialog", timeout=2000) as event_info:
            inp.press("Enter")

        dialog = event_info.value
        #print("Dialog message:", dialog.message)
        dialog.dismiss()
        return True

    except PWTimeoutError:
        return False


