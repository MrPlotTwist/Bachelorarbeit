import requests
import time

def test_bruteforce_protection(login_url: str, email: str, attempts: int):
    baseline_status = None
    baseline_body = None
    protection_detected = False

    for i in range(attempts):
        payload = {
            "email": email,
            "password": f"wrong-password-{i}"
        }

        try:
            r = requests.post(
                login_url,
                json=payload,
                timeout=10,
                allow_redirects=False
            )

            status_code = r.status_code
            body_snippet = r.text[:200]
            retry_after = r.headers.get("Retry-After")

            if baseline_status is None:
                baseline_status = status_code
                baseline_body = body_snippet

            body_changed = body_snippet != baseline_body
            status_changed = status_code != baseline_status

            print(
                f"Attempt {i+1}: "
                f"status={status_code}, "
                f"retry_after={retry_after}, "
                f"body_changed={body_changed}, "
                f"status_changed={status_changed}"
            )

            if body_changed or status_changed or retry_after is not None:
                protection_detected = True

        except requests.RequestException as ex:
            print(f"Attempt {i+1}: ERROR {ex}")

        time.sleep(0.2)

    return protection_detected