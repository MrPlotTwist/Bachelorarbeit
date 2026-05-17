from __future__ import annotations

import json
from playwright.sync_api import Playwright

from app.crawler_logic.crawling_links import is_crawable, is_in_scope, to_absolute
from app.crawler_logic.extracting_forms import extract_forms
from app.crawler_logic.helper_functions import dismiss_popups
from app.db.database import create_run, init_db, insert_into_forms, insert_into_targets

init_db()

#Testfunktion um nur Links zu crawlen, aber nicht auf Schwachstellen testen
def crawl_urls_without_vuls(playwright: Playwright, start_url: str, max_pages: int):
    browser = playwright.chromium.launch(headless=True)

    run_id = create_run(start_url=start_url)

    visited_anon: set[str] = set()
    visited_auth: set[str] = set() 
    queue: list[str] = [start_url]
    all_forms: list[dict] = []

    try:
        while queue and len(visited_anon) < max_pages:
            url = queue.pop(0)

            if url in visited_anon:
                continue

            visited_anon.add(url)
            page = browser.new_page()

            try:
                response = page.goto(url, wait_until="domcontentloaded", timeout=30_000)
                page.wait_for_timeout(800)

                print(f"PAGE URL: {page.url}")
                print(f"LENGTHS OF VISITED: {len(visited_anon)}")
                print(f"LENGTHS OF QUEUE: {len(queue)}")

                dismiss_popups(page)

                headers = response.all_headers() if response else {}
                headers_json = json.dumps(headers, ensure_ascii=False)

                target_id = insert_into_targets(
                    base_url=page.url,
                    run_id=run_id,
                    headers_json=headers_json
                )

                forms_on_page = extract_forms(page)
                all_forms.extend(forms_on_page)

                for form in forms_on_page:
                    insert_into_forms(
                        target_id=target_id,
                        page_url=form.get("url") or page.url,
                        action_url=form.get("action"),
                        method=form.get("method"),
                        form_name=form.get("intent") or form.get("type"),
                        form_structure_json=json.dumps(form, ensure_ascii=False)
                    )

                try:
                    hrefs = page.evaluate("""
                    () => Array.from(document.querySelectorAll('a[href]'))
                        .map(a => a.getAttribute('href'))
                        .filter(href => href && href.trim() !== '')
                    """)
                except Exception as e:
                    print(f"Fehler beim Einsammeln der Links auf {page.url}: {e}")
                    hrefs = []

                for href in hrefs:
                    if not is_crawable(href):
                        continue

                    abs_url = to_absolute(page.url, href)

                    if (
                        abs_url
                        and abs_url not in visited_anon
                        and abs_url not in queue
                        and is_in_scope(start_url, abs_url)
                    ):
                        queue.append(abs_url)

            finally:
                if not page.is_closed():
                    page.close()

        return run_id, visited_anon, visited_auth, all_forms

    finally:
        browser.close()