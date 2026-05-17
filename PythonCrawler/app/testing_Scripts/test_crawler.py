from playwright.sync_api import sync_playwright
from app.crawler_logic.crawler import crawl_urls
from app.db.database import get_run_results
from app.ai_integration.gpt_init import gpt_output

if __name__ == "__main__":
    with sync_playwright() as pw:
        run_id = crawl_urls(
            pw,
            "http://localhost:3000",
            15
        )
        print("\n" + "=" * 80)
        print("OUTPUT OF DB")
        print("=" * 80)

        db_results = get_run_results(run_id)

        #Zusammenfassung
        print("\n" + "=" * 80)
        print("ZUSAMMENFASSUNG ALLER GECRAWLTEN URLS")
        print("=" * 80)

        for i, entry in enumerate(db_results["targets"], start=1):
            url = entry["target"][2]
            print(f"{i}. {url}")

        print(f"\nGesamtzahl gecrawlter URLs: {len(db_results['targets'])}")

        run = db_results["run"]
        print("\nRUN:")
        print(run)

        for i, entry in enumerate(db_results["targets"], start=1):
            print(f"\nTARGET #{i}")
            print("Target:", entry["target"])

            print("\nForms:")
            for form in entry["forms"]:
                print(form)

            print("\nVulnerabilities:")
            for vuln in entry["vulnerabilities"]:
                print(vuln)

            print("\nCredentials:")
            for cred in entry["credentials"]:
                print(cred)

        print("=" * 60)
        print("GPT OUTPUT STARTS HERE:")
        gpt_output(db_output=db_results, run_id=run_id)