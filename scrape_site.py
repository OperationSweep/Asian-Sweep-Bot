"""Generic website scraper.

Crawls a site from a starting URL and, for every page it reaches, saves the
raw HTML, the extracted plain text, any HTML tables as CSV, and a JSON index
describing the whole crawl.

Standard library only, so there is nothing to install:

    python3 scrape_site.py http://172.27.88.110:8350/ --out scraped

Targets on a private network (RFC1918 addresses, VPN-only hosts) are only
reachable from a machine on that network, so run this there.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import sys
import time
import urllib.error
import urllib.request
import urllib.robotparser
from collections import deque
from dataclasses import dataclass, field
from html.parser import HTMLParser
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from urllib.parse import urldefrag, urljoin, urlparse

DEFAULT_USER_AGENT = "scrape_site/1.0 (+stdlib urllib)"

# Content of these elements is markup or styling, never page text.
SKIP_TAGS = {"script", "style", "noscript", "template", "svg", "head"}

# Elements that imply a line break in the extracted text.
BLOCK_TAGS = {
    "address", "article", "aside", "blockquote", "br", "div", "dd", "dl", "dt",
    "fieldset", "figcaption", "figure", "footer", "form", "h1", "h2", "h3",
    "h4", "h5", "h6", "header", "hr", "li", "main", "nav", "ol", "p", "pre",
    "section", "table", "tbody", "tfoot", "thead", "tr", "ul",
}

# Cells stay on their row, separated by a tab.
CELL_TAGS = {"td", "th"}


class PageParser(HTMLParser):
    """Single pass over a page: title, text, links and tables."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.title: str = ""
        self.links: List[str] = []
        self.tables: List[List[List[str]]] = []
        self._text: List[str] = []
        self._skip_depth = 0
        self._in_title = False
        self._table_stack: List[List[List[str]]] = []
        self._row: Optional[List[str]] = None
        self._cell: Optional[List[str]] = None

    # -- helpers ---------------------------------------------------------
    def _close_cell(self) -> None:
        if self._cell is not None and self._row is not None:
            self._row.append(normalize_inline(" ".join(self._cell)))
        self._cell = None

    def _close_row(self) -> None:
        self._close_cell()
        if self._row is not None and self._table_stack:
            self._table_stack[-1].append(self._row)
        self._row = None

    # -- HTMLParser hooks ------------------------------------------------
    def handle_starttag(self, tag: str, attrs: List[Tuple[str, Optional[str]]]) -> None:
        if tag in SKIP_TAGS:
            self._skip_depth += 1
            return
        if tag == "title":
            self._in_title = True
        elif tag == "a":
            for name, value in attrs:
                if name == "href" and value:
                    self.links.append(value.strip())
        elif tag == "table":
            self._table_stack.append([])
        elif tag == "tr" and self._table_stack:
            self._close_row()
            self._row = []
        elif tag in ("td", "th") and self._row is not None:
            self._close_cell()
            self._cell = []

        if not self._skip_depth:
            if tag in BLOCK_TAGS:
                self._text.append("\n")
            elif tag in CELL_TAGS:
                self._text.append("\t")

    def handle_endtag(self, tag: str) -> None:
        if tag in SKIP_TAGS:
            self._skip_depth = max(0, self._skip_depth - 1)
            return
        if tag == "title":
            self._in_title = False
        elif tag in ("td", "th"):
            self._close_cell()
        elif tag == "tr":
            self._close_row()
        elif tag == "table" and self._table_stack:
            self._close_row()
            table = self._table_stack.pop()
            if table:
                self.tables.append(table)

        if tag in BLOCK_TAGS and not self._skip_depth:
            self._text.append("\n")

    def handle_data(self, data: str) -> None:
        if self._in_title:
            self.title += data
        if self._skip_depth:
            return
        self._text.append(data)
        if self._cell is not None:
            self._cell.append(data)

    # -- results ---------------------------------------------------------
    def text(self) -> str:
        raw = "".join(self._text)
        lines = [normalize_inline(line) for line in raw.split("\n")]
        out: List[str] = []
        for line in lines:
            if line or (out and out[-1]):
                out.append(line)
        return "\n".join(out).strip()


def normalize_inline(value: str) -> str:
    """Collapse runs of whitespace inside a single line of text."""
    return re.sub(r"\s+", " ", value).strip()


@dataclass
class PageResult:
    url: str
    depth: int
    final_url: str = ""
    status: Optional[int] = None
    content_type: str = ""
    title: str = ""
    bytes: int = 0
    error: str = ""
    duplicate_of: str = ""
    html_path: str = ""
    text_path: str = ""
    table_paths: List[str] = field(default_factory=list)
    links: List[str] = field(default_factory=list)


def slug_for(url: str) -> str:
    """Filesystem-safe, collision-resistant stem for a URL."""
    parsed = urlparse(url)
    raw = (parsed.path or "/").strip("/")
    if parsed.query:
        raw = f"{raw}__{parsed.query}"
    stem = re.sub(r"[^A-Za-z0-9._-]+", "_", raw).strip("_") or "index"
    digest = hashlib.sha1(url.encode("utf-8")).hexdigest()[:8]
    return f"{stem[:60]}-{digest}"


def charset_from(content_type: str, body: bytes) -> str:
    match = re.search(r"charset=([\w-]+)", content_type, re.I)
    if match:
        return match.group(1)
    match = re.search(rb'charset=["\']?([\w-]+)', body[:4096], re.I)
    if match:
        return match.group(1).decode("ascii", "replace")
    return "utf-8"


def in_scope(url: str, base_host: str, allow_subdomains: bool) -> bool:
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        return False
    host = parsed.netloc.lower()
    if host == base_host:
        return True
    return allow_subdomains and host.endswith("." + base_host.split(":")[0])


def load_robots(start_url: str, user_agent: str, timeout: float):
    """Return a robots parser, or None when robots.txt is unavailable."""
    parsed = urlparse(start_url)
    robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
    parser = urllib.robotparser.RobotFileParser()
    parser.set_url(robots_url)
    try:
        request = urllib.request.Request(robots_url, headers={"User-Agent": user_agent})
        with urllib.request.urlopen(request, timeout=timeout) as response:
            body = response.read().decode("utf-8", "replace")
        parser.parse(body.splitlines())
        return parser
    except Exception:
        return None


def fetch(url: str, user_agent: str, timeout: float, max_bytes: int):
    request = urllib.request.Request(url, headers={"User-Agent": user_agent})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            body = response.read(max_bytes + 1)
            return response.getcode(), response.headers.get("Content-Type", ""), body, response.geturl(), ""
    except urllib.error.HTTPError as exc:
        body = exc.read(max_bytes + 1) if exc.fp else b""
        return exc.code, exc.headers.get("Content-Type", "") if exc.headers else "", body, url, f"HTTP {exc.code} {exc.reason}"
    except Exception as exc:  # timeouts, DNS, refused connections
        return None, "", b"", url, f"{type(exc).__name__}: {exc}"


def crawl(args: argparse.Namespace) -> int:
    out_dir = Path(args.out)
    html_dir, text_dir, table_dir = out_dir / "html", out_dir / "text", out_dir / "tables"
    for directory in (html_dir, text_dir, table_dir):
        directory.mkdir(parents=True, exist_ok=True)

    base_host = urlparse(args.url).netloc.lower()
    robots = None if args.ignore_robots else load_robots(args.url, args.user_agent, args.timeout)

    queue: deque = deque([(urldefrag(args.url).url, 0)])
    seen = {queue[0][0]}
    seen_bodies: Dict[str, str] = {}
    results: List[PageResult] = []

    while queue and len(results) < args.max_pages:
        url, depth = queue.popleft()
        if robots is not None and not robots.can_fetch(args.user_agent, url):
            print(f"[robots] skip {url}", file=sys.stderr)
            continue

        status, content_type, body, final_url, error = fetch(
            url, args.user_agent, args.timeout, args.max_bytes
        )
        result = PageResult(
            url=url, depth=depth, final_url=final_url, status=status,
            content_type=content_type, bytes=len(body), error=error,
        )
        print(f"[{status or 'ERR'}] d{depth} {url}" + (f" -- {error}" if error else ""))

        body_hash = hashlib.sha1(body).hexdigest() if body else ""
        if body_hash and body_hash in seen_bodies:
            result.duplicate_of = seen_bodies[body_hash]
            results.append(result)
            print(f"        duplicate of {result.duplicate_of}")
            continue

        if body and "html" in content_type.lower():
            seen_bodies[body_hash] = url
            html = body.decode(charset_from(content_type, body), "replace")
            parser = PageParser()
            parser.feed(html)
            parser.close()
            result.title = normalize_inline(parser.title)

            stem = slug_for(url)
            html_file = html_dir / f"{stem}.html"
            html_file.write_text(html, encoding="utf-8")
            result.html_path = str(html_file.relative_to(out_dir))

            text_file = text_dir / f"{stem}.txt"
            text_file.write_text(parser.text(), encoding="utf-8")
            result.text_path = str(text_file.relative_to(out_dir))

            for index, table in enumerate(parser.tables, start=1):
                table_file = table_dir / f"{stem}-{index}.csv"
                with table_file.open("w", encoding="utf-8", newline="") as handle:
                    csv.writer(handle).writerows(table)
                result.table_paths.append(str(table_file.relative_to(out_dir)))

            for href in parser.links:
                target = urldefrag(urljoin(final_url, href)).url
                result.links.append(target)
                if target in seen or depth >= args.max_depth:
                    continue
                if not in_scope(target, base_host, args.allow_subdomains):
                    continue
                seen.add(target)
                queue.append((target, depth + 1))

        results.append(result)
        if queue and args.delay > 0:
            time.sleep(args.delay)

    index = {
        "start_url": args.url,
        "pages_fetched": len(results),
        "pages_queued_unvisited": len(queue),
        "settings": {
            "max_pages": args.max_pages, "max_depth": args.max_depth,
            "delay": args.delay, "allow_subdomains": args.allow_subdomains,
            "robots_respected": robots is not None,
        },
        "pages": [vars(page) for page in results],
    }
    (out_dir / "index.json").write_text(json.dumps(index, indent=2), encoding="utf-8")

    ok = sum(1 for page in results if page.status == 200)
    tables = sum(len(page.table_paths) for page in results)
    print(
        f"\nDone. {ok}/{len(results)} pages OK, {tables} tables extracted -> {out_dir}/",
        file=sys.stderr,
    )
    return 0 if ok else 1


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("url", help="Starting URL, e.g. http://172.27.88.110:8350/")
    parser.add_argument("--out", default="scraped", help="Output directory (default: scraped)")
    parser.add_argument("--max-pages", type=int, default=50, help="Stop after this many pages (default: 50)")
    parser.add_argument("--max-depth", type=int, default=2, help="Link depth from the start URL (default: 2)")
    parser.add_argument("--delay", type=float, default=0.5, help="Seconds between requests (default: 0.5)")
    parser.add_argument("--timeout", type=float, default=15.0, help="Per-request timeout in seconds (default: 15)")
    parser.add_argument("--max-bytes", type=int, default=5_000_000, help="Max response body to read (default: 5MB)")
    parser.add_argument("--user-agent", default=DEFAULT_USER_AGENT, help="User-Agent header to send")
    parser.add_argument("--allow-subdomains", action="store_true", help="Also follow links to subdomains")
    parser.add_argument("--ignore-robots", action="store_true", help="Do not consult robots.txt")
    return parser.parse_args(argv)


def main(argv: Optional[List[str]] = None) -> int:
    return crawl(parse_args(argv))


if __name__ == "__main__":
    sys.exit(main())
