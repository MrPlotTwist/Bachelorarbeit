from __future__ import annotations
from app.db.database import *
import json
from playwright.sync_api import Playwright

#all included files
from app.ai_integration.gpt_init import *
from app.ai_integration.pdf_init import *
from app.crawler_logic.crawling_links import *
from app.crawler_logic.extracting_forms import *
from app.crawler_logic.helper_functions import *
from app.crawler_logic.models import *
from app.db.database import *
from app.vul_checks.broken_auth_check import *
from app.vul_checks.bruteforce_check import *
from app.vul_checks.injection_check import *
from app.vul_checks.xss_check import *

#datenbankerstellung
init_db()


# ----------------------------
# Crawl
# ----------------------------
def crawl_urls(playwright: Playwright, start_url: str, max_pages: int):
    browser = playwright.chromium.launch(headless=True)

    run_id = create_run()

    #DEBUG MODE
    #browser = playwright.chromium.launch(
    #headless=False,
    #slow_mo=200
    #)

    visited_anon: set[str] = set()
    visited_auth: set[str] = set()
    queue: list[str] = [start_url]
    all_forms: list[dict] = []
    loginURL = None
    is_xss = False
    xss_URL = None
    login_form_id = None


    try:
        # Phase 1: anon crawl
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
                #page.pause()
                #header auslesen
                headers = response.all_headers() if response else {}
                headers_json = json.dumps(headers, ensure_ascii=False)

                #targets speichern in database
                target_id = insert_into_targets(base_url=page.url, run_id=run_id,headers_json=headers_json)

                forms_on_page = extract_forms(page)
                all_forms.extend(forms_on_page)

                #forms speichern
                saved_forms = []
                for form in forms_on_page:
                    form_id = insert_into_forms(target_id=target_id, page_url=form.get("url") or page.url, action_url=form.get("action"), method=form.get("method"), form_name=form.get("intent") or form.get("type"), form_structure_json=json.dumps(form))
                    saved_forms.append((form, form_id))

                if "login" in page.url:
                    loginURL = page.url

                    #login form herausfiltern
                    for form, form_id in saved_forms:
                        if is_login_form(form):
                            login_form_id = form_id
                            login_target_id = target_id
                            break

                # Links sammeln
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

                    #url überprüfen, dann in queue speichern
                    if (
                        abs_url
                        and abs_url not in visited_anon
                        and abs_url not in queue
                        and is_in_scope(start_url, abs_url)
                    ):
                        queue.append(abs_url)

                #auf jeder URL xss versuchen
                if xss_URL == None:
                    #xss testen
                    is_xss = xss_validation(page)

                #xss daten in DB speichern
                if is_xss and xss_URL != page.url:
                    xss_URL = page.url
                    print(f"xss_URL: {xss_URL}")
                    print(f"XSS is possible on PageURL: {page.url}")
                    is_xss = False
                    insert_into_vulnerabilities(
                        target_id=target_id,
                        form_id=None,
                        page_url=page.url,
                        vul_type="XSS Injection",
                        severity="high",
                        parameter_name="search-input",
                        payload="<iframe src='javascript:alert(`xss`)'>",
                        evidence="Alert message is triggered at input"
                                )

            finally:
                #page.pause()
                page.close()

        # 2. phase mit auth
        if loginURL:
            print(f"LOGINURL: {loginURL}")

            auth_context = browser.new_context()
            auth_page = auth_context.new_page()

            login_token = None

            try:
                auth_page.goto(loginURL, wait_until="domcontentloaded", timeout=30_000)
                auth_page.wait_for_timeout(800)
                dismiss_popups(auth_page)

                #injection probieren
                injection_success = tryInjection(auth_page)

                if injection_success:
                    auth_page.wait_for_timeout(1000)

                    #token filtern, dann in DB speichern
                    login_token = auth_page.evaluate(
                        "() => window.localStorage.getItem('token')"
                    )

                    insert_into_vulnerabilities(
                        target_id=login_target_id,
                        form_id=login_form_id,
                        page_url=auth_page.url,
                        vul_type="SQL Injection",
                        severity="critical",
                        parameter_name="email",
                        payload="' OR 1=1 --",
                        evidence="Login bypass via SQL injection"
                    )

                    insert_into_discovered_credentials(
                        target_id=login_target_id,
                        form_id=login_form_id,
                        login_token=login_token,
                        username="' OR 1=1 --",
                        password="a"
                    )

                    # Bruteforce-Test einmalig
                    try:
                        bruteforce_protection_active = test_bruteforce_protection(
                            start_url + "/rest/user/login",
                            "test@example.com",
                            attempts=40
                        )

                        if not bruteforce_protection_active:
                            insert_into_vulnerabilities(
                                target_id=login_target_id,
                                form_id=login_form_id,
                                page_url=loginURL,
                                vul_type="missing_bruteforce_protection",
                                severity="medium",
                                parameter_name="email/password",
                                payload="40 failed login attempts",
                                evidence="Keine Änderung von Statuscode, Response-Body oder Retry-After nach 40 fehlgeschlagenen Login-Versuchen"
                            )
                    except Exception as ex:
                        print(f"Fehler beim Bruteforce-Test: {ex}")

                    # Broken-Auth-Tests einmalig
                    if login_token:
                        try:
                            #tokenlogik checken
                            auth_findings = test_broken_auth(
                                base_url=start_url,
                                valid_token=login_token
                            )

                            #gefunde VULs in DB speichern
                            for finding in auth_findings:
                                insert_into_vulnerabilities(
                                    target_id=login_target_id,
                                    form_id=login_form_id,
                                    page_url=loginURL,
                                    vul_type=finding["type"],
                                    severity=finding["severity"],
                                    parameter_name="Authorization",
                                    payload="Bearer <token>",
                                    evidence=finding["evidence"]
                                )
                        except Exception as ex:
                            print(f"Fehler bei Broken-Auth-Tests: {ex}")

                    #crawler ab hier mit token als context
                    queue = [start_url]

                    while queue and len(visited_auth) < max_pages:
                        print("got into loop...")
                        url = queue.pop(0)

                        if url in visited_auth:
                            continue

                        visited_auth.add(url)

                        page = auth_context.new_page()

                        try:
                            response = page.goto(url, wait_until="domcontentloaded", timeout=30_000)
                            page.wait_for_timeout(800)
                            dismiss_popups(page)

                            print(f"PAGE URL: {page.url}")
                            print(f"LENGTHS OF VISITED: {len(visited_auth)}")
                            print(f"LENGTHS OF QUEUE: {len(queue)}")

                            #header auslesen
                            headers = response.all_headers() if response else {}
                            headers_json = json.dumps(headers, ensure_ascii=False)

                            # speichern in database
                            target_id = insert_into_targets(
                                base_url=page.url,
                                run_id=run_id,
                                headers_json=headers_json
                            )

                            forms_on_page = extract_forms(page)
                            all_forms.extend(forms_on_page)

                            #forms in db speichern
                            for form in forms_on_page:
                                insert_into_forms(
                                    target_id=target_id,
                                    page_url=form.get("url") or page.url,
                                    action_url=form.get("action"),
                                    method=form.get("method"),
                                    form_name=form.get("intent") or form.get("type"),
                                    form_structure_json=json.dumps(form)
                                )

                            # Links sammeln
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
                                    and abs_url not in visited_auth
                                    and abs_url not in queue
                                    and is_in_scope(start_url, abs_url)
                                ):
                                    queue.append(abs_url)

                        finally:
                            page.close()

            finally:
                auth_page.close()
                auth_context.close()
                    
                    
                return run_id


    finally:
        browser.close()