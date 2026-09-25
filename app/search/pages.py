import ipaddress
import json
import re
import socket
from datetime import timezone, timedelta
from urllib.parse import urlsplit, urlunsplit, urljoin, parse_qsl, urlencode
import httpx
import tldextract
from bs4 import BeautifulSoup
from dateutil.parser import isoparse
from app.search.base import PageProvider

EXTRACT = tldextract.TLDExtract(suffix_list_urls=(), cache_dir=None, include_psl_private_domains=True)
BLOCKED = {"t.me", "telegram.org", "facebook.com", "instagram.com", "linkedin.com", "x.com", "twitter.com"}


def domain(url):
    host = urlsplit(url).hostname or ""
    result = EXTRACT(host)
    return result.top_domain_under_public_suffix or host.lower()


def valid_url(url):
    try:
        if re.search(r'[\s<>"\\]', url):
            return False
        p = urlsplit(url)
        return bool(p.scheme in {"http", "https"} and p.hostname and not p.username and not p.password
                    and p.port in {None, 80, 443} and domain(url) not in BLOCKED)
    except ValueError:
        return False


def canonical_url(url):
    p = urlsplit(url)
    query = [(k, v) for k, v in parse_qsl(p.query) if not k.lower().startswith("utm_") and k not in {"fbclid", "gclid"}]
    return urlunsplit((p.scheme.lower(), p.netloc.lower(), p.path.rstrip("/") or "/", urlencode(sorted(query)), ""))


def public_url(url):
    return bool(public_addresses(url))


def public_addresses(url):
    if not valid_url(url):
        return []
    try:
        host = urlsplit(url).hostname
        addresses = socket.getaddrinfo(host, None, type=socket.SOCK_STREAM)
        ips = list(dict.fromkeys(a[4][0] for a in addresses))
        return ips if ips and all(ipaddress.ip_address(ip).is_global for ip in ips) else []
    except (OSError, ValueError):
        return []


def parse_date(value):
    try:
        dt = isoparse(value)
        if len(value.strip()) == 10:
            return dt.replace(tzinfo=timezone.utc), "day"
        if dt.tzinfo is None:
            return None, "unknown"  # Never silently infer publisher timezone.
        return dt.astimezone(timezone.utc), "exact"
    except (ValueError, TypeError, OverflowError):
        return None, "unknown"


def article_data(html):
    soup = BeautifulSoup(html, "html.parser")
    dates = []
    publication_names = {"article:published_time", "datepublished", "date", "pubdate",
                         "publishdate", "publish-date", "sailthru.date", "parsely-pub-date"}
    for meta in soup.find_all("meta"):
        if (meta.get("property") or meta.get("name", "")).lower() in publication_names:
            dates.append(meta.get("content", ""))
    def walk(obj):
        if isinstance(obj, dict):
            if "datePublished" in obj:
                dates.append(str(obj["datePublished"]))
            for val in obj.values():
                walk(val)
        elif isinstance(obj, list):
            for val in obj:
                walk(val)
    for script in soup.find_all("script", type="application/ld+json"):
        try:
            walk(json.loads(script.string or ""))
        except (ValueError, RecursionError):
            continue
    # Card/recommendation timestamps are not metadata for the current article.
    # Use visible time elements only when publication metadata is unavailable.
    if not any(parse_date(value)[0] is not None for value in dates):
        time_scope = soup.find("article") or soup.find("main") or soup
        for t in time_scope.select('time[datetime]'):
            dates.append(t.get("datetime", t.get_text()))
    parsed = [(raw, *parse_date(raw)) for raw in dates]
    parsed = [x for x in parsed if x[1] is not None]
    # Conflicting metadata is not trustworthy enough for automatic inclusion.
    date, precision, evidence = None, "unknown", ""
    if parsed and len({x[1].date() for x in parsed}) == 1 and len({x[1] for x in parsed if x[2] == "exact"}) <= 1:
        raw, date, precision = sorted(parsed, key=lambda x: x[2] != "exact")[0]
        evidence = "Page publication metadata: " + raw
    for node in soup(["script", "style", "nav", "footer", "header", "form"]):
        node.decompose()
    body = soup.find("article") or soup.find("main") or soup
    content = re.sub(r"\s+", " ", body.get_text(" ", strip=True))[:6000]
    return content, date, precision, evidence


def in_window(source, start, end):
    if source.published_at is None or not source.date_evidence:
        return False
    if source.date_precision == "day":
        # Unknown timezone + unknown time: require the entire possible UTC interval to fit.
        return start <= source.published_at - timedelta(hours=14) and source.published_at + timedelta(hours=36) <= end
    return source.date_precision == "exact" and start <= source.published_at <= end


class WebPages(PageProvider):
    def __init__(self, max_fetches=80, client=None):
        self.client = client or httpx.Client(timeout=20, follow_redirects=False, trust_env=False,
            limits=httpx.Limits(max_keepalive_connections=0),
            headers={"User-Agent": "AIIntelligenceResearch/0.1"})
        self.max_fetches = max_fetches
        self.calls = 0
        self.cache = {}

    def fetch(self, source):
        key = canonical_url(source.url)
        if key in self.cache:
            return self.cache[key]
        result = source.model_copy(update={"published_at": None, "date_precision": "unknown", "date_evidence": ""})
        try:
            if self.calls >= self.max_fetches:
                raise ValueError("Page fetch budget exhausted")
            self.calls += 1
            url = source.url
            for _ in range(4):
                addresses = public_addresses(url)
                if not addresses:
                    raise ValueError("Non-public or disallowed URL")
                # Pin the validated IP: a second DNS lookup must not bypass the private-IP gate.
                parsed = urlsplit(url)
                ip = addresses[0]
                netloc = f"[{ip}]" if ":" in ip else ip
                if parsed.port:
                    netloc += f":{parsed.port}"
                pinned = urlunsplit((parsed.scheme, netloc, parsed.path, parsed.query, ""))
                with self.client.stream("GET", pinned, headers={"Host": parsed.netloc},
                                        extensions={"sni_hostname": parsed.hostname}) as response:
                    if response.is_redirect:
                        url = urljoin(url, response.headers.get("location", ""))
                        continue
                    if response.status_code != 200:
                        raise ValueError(f"Page HTTP {response.status_code}")
                    if "html" not in response.headers.get("content-type", ""):
                        raise ValueError("Only public HTML articles are supported")
                    chunks, size = [], 0
                    for chunk in response.iter_bytes():
                        size += len(chunk)
                        if size > 2_000_000:
                            raise ValueError("Page too large")
                        chunks.append(chunk)
                    content, date, precision, evidence = article_data(b"".join(chunks).decode(response.encoding or "utf-8", errors="replace"))
                    result = result.model_copy(update={"content": content, "published_at": date,
                        "date_precision": precision, "date_evidence": evidence, "fetched": bool(content),
                        "source": domain(url)})
                    break
            else:
                raise ValueError("Too many redirects")
        except (httpx.HTTPError, ValueError, OSError) as exc:
            result = result.model_copy(update={"fetch_error": str(exc) if isinstance(exc, ValueError) else type(exc).__name__})
        self.cache[key] = result
        return result
