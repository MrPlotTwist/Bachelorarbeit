#-------------------------
#crawling links logic
#---------------------------
from __future__ import annotations
from urllib.parse import urljoin, urlparse

#die basisurl beibehalten
def is_crawable(href: str) -> bool:
    if not href:
        return False
    href = href.strip()
    low = href.lower()

    if low == "#":
        return False
    if href.startswith("#/"):
        return True
    if href.startswith("#"):
        return False

    if low.startswith(("javascript:", "mailto:", "tel:")):
        return False
    
    if "redirect?" in low:
        return False

    return True

def default_port(scheme: str) -> int:
    return 443 if scheme == "https" else 80

#überprüfen ob nächste URL im Scope ist
def is_in_scope(baseurl: str, nexturl: str) -> bool:
    b = urlparse(baseurl)
    n = urlparse(nexturl)

    if n.scheme not in ("http", "https"):
        return False

    b_port = b.port or default_port(b.scheme)
    n_port = n.port or default_port(n.scheme)

    return (b.hostname == n.hostname) and (b_port == n_port)

#macht aus link eine absolute URL
def to_absolute(base: str, href: str) -> str | None:
    if not href:
        return None
    href = href.strip()
    low = href.lower()

    if low.startswith(("javascript:", "mailto:", "tel:")):
        return None

    if href.startswith("#/"):
        base_no_frag = base.split("#", 1)[0]
        return base_no_frag + href

    if href.startswith("#"):
        return None

    #url Zusammenfügen
    absolute = urljoin(base, href)
    parsed = urlparse(absolute)
    if parsed.scheme not in ("http", "https"):
        return None
    return absolute
