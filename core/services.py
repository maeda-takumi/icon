import json
import re
import urllib.parse
import urllib.request
import webbrowser
from pathlib import Path
from typing import Optional

from PySide6.QtGui import QPixmap

APP_NAME = "URL Launcher"
DATA_DIR = Path.home() / ".url_launcher_sample"
DATA_FILE = DATA_DIR / "links.json"
ICON_CACHE_DIR = DATA_DIR / "icons"

DEFAULT_DATA = {
    "groups": [
        {"id": 1, "name": "仕事"},
        {"id": 2, "name": "開発"},
        {"id": 3, "name": "AI"},
    ],
    "links": [
        {"id": 1, "group_id": 1, "title": "Google Drive", "url": "https://drive.google.com/"},
        {"id": 2, "group_id": 1, "title": "Google Sheets", "url": "https://docs.google.com/spreadsheets/"},
        {"id": 3, "group_id": 2, "title": "GitHub", "url": "https://github.com/"},
        {"id": 4, "group_id": 2, "title": "Localhost", "url": "http://localhost/"},
        {"id": 5, "group_id": 3, "title": "ChatGPT", "url": "https://chatgpt.com/"},
    ],
}


def get_domain_text(url: str) -> str:
    parsed = urllib.parse.urlparse(url)
    host = parsed.netloc or parsed.path
    host = host.replace("www.", "")
    return host or url

def get_icon_fetch_host(url: str) -> str:
    parsed = urllib.parse.urlparse(url)
    return parsed.netloc or parsed.path


def get_initial_text(title: str, url: str) -> str:
    if title.strip():
        return title.strip()[0].upper()
    domain = get_domain_text(url)
    return domain[0].upper() if domain else "?"


class LinkService:
    def __init__(self):
        self.data = self.load_data()
        self.icon_cache: dict[str, QPixmap] = {}

    def ensure_data_file(self):
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        ICON_CACHE_DIR.mkdir(parents=True, exist_ok=True)
        if not DATA_FILE.exists():
            with open(DATA_FILE, "w", encoding="utf-8") as f:
                json.dump(DEFAULT_DATA, f, ensure_ascii=False, indent=2)

    def load_data(self):
        self.ensure_data_file()
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)

    def save(self):
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)

    def open_url(self, url: str):
        webbrowser.open(url)

    def open_urls(self, urls: list[str]):
        for url in urls:
            webbrowser.open(url)

    def get_groups(self):
        return self.data["groups"]

    def get_links_by_group(self, group_id: int):
        return [link for link in self.data["links"] if link["group_id"] == group_id]

    def get_filtered_links(self, group_id: Optional[int], keyword: str):
        if group_id is None:
            return []

        links = self.get_links_by_group(group_id)
        keyword = keyword.strip().lower()
        if not keyword:
            return links

        return [
            link
            for link in links
            if keyword in link["title"].lower() or keyword in get_domain_text(link["url"]).lower()
        ]

    def next_group_id(self):
        return max((g["id"] for g in self.data["groups"]), default=0) + 1

    def next_link_id(self):
        return max((l["id"] for l in self.data["links"]), default=0) + 1

    def add_group(self, name: str):
        group = {"id": self.next_group_id(), "name": name.strip()}
        self.data["groups"].append(group)
        self.save()
        return group

    def delete_group(self, group_id: int):
        self.data["groups"] = [g for g in self.data["groups"] if g["id"] != group_id]
        self.data["links"] = [l for l in self.data["links"] if l["group_id"] != group_id]
        self.save()

    def add_link(self, group_id: int, title: str, url: str):
        self.data["links"].append(
            {
                "id": self.next_link_id(),
                "group_id": group_id,
                "title": title,
                "url": url,
            }
        )
        self.save()

    def update_link(self, link_id: int, title: str, url: str):
        link = self.find_link(link_id)
        if not link:
            return
        link["title"] = title
        link["url"] = url
        self.save()

    def delete_link(self, link_id: int):
        self.data["links"] = [l for l in self.data["links"] if l["id"] != link_id]
        self.save()

    def find_link(self, link_id: int):
        return next((l for l in self.data["links"] if l["id"] == link_id), None)

    def _cache_file(self, url: str) -> Path:
        key = urllib.parse.quote(url, safe="")
        return ICON_CACHE_DIR / f"{key}.png"

    @staticmethod
    def _extract_icon_links(page_url: str, html_bytes: bytes) -> list[str]:
        try:
            html = html_bytes.decode("utf-8", errors="ignore")
        except Exception:
            return []

        links: list[str] = []
        link_tag_pattern = re.compile(r"<link\b[^>]*>", re.IGNORECASE)
        rel_pattern = re.compile(r"""rel\s*=\s*(?:"([^"]+)"|'([^']+)'|([^\s>]+))""", re.IGNORECASE)
        href_pattern = re.compile(r"""href\s*=\s*(?:"([^"]+)"|'([^']+)'|([^\s>]+))""", re.IGNORECASE)

        for tag in link_tag_pattern.findall(html):
            rel_match = rel_pattern.search(tag)
            href_match = href_pattern.search(tag)
            if not rel_match or not href_match:
                continue

            rel_raw = next((value for value in rel_match.groups() if value), "")
            rel_values = {part.strip().lower() for part in rel_raw.split()}
            if (
                "icon" not in rel_values
                and "apple-touch-icon" not in rel_values
                and "mask-icon" not in rel_values
            ):
                continue

            href = next((value for value in href_match.groups() if value), "").strip()
            if not href:
                continue
            links.append(urllib.parse.urljoin(page_url, href))

        return links

    @staticmethod
    def _dedupe_keep_order(urls: list[str]) -> list[str]:
        seen: set[str] = set()
        deduped: list[str] = []
        for item in urls:
            if item in seen:
                continue
            seen.add(item)
            deduped.append(item)
        return deduped

    def _build_icon_candidates(self, url: str) -> list[str]:
        host = get_icon_fetch_host(url)
        root_https = f"https://{host}"
        root_http = f"http://{host}"
        candidates = [
            f"{root_https}/favicon.ico",
            f"{root_http}/favicon.ico",
            f"{root_https}/favicon.png",
            f"{root_http}/favicon.png",
            f"{root_https}/apple-touch-icon.png",
            f"{root_http}/apple-touch-icon.png",
            f"{root_https}/apple-touch-icon-precomposed.png",
            f"{root_http}/apple-touch-icon-precomposed.png",
        ]

        page_bytes: Optional[bytes] = None
        request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        try:
            with urllib.request.urlopen(request, timeout=5) as response:
                page_bytes = response.read()
        except Exception:
            page_bytes = None

        if page_bytes:
            candidates.extend(self._extract_icon_links(url, page_bytes))

        encoded_url = urllib.parse.quote(url, safe=':/?=&')
        candidates.extend(
            [
                f"https://www.google.com/s2/favicons?sz=64&domain_url={encoded_url}",
                f"https://icons.duckduckgo.com/ip3/{host}.ico",
            ]
        )
        return self._dedupe_keep_order(candidates)
    
    def get_favicon(self, url: str) -> Optional[QPixmap]:
        if url in self.icon_cache:
            return self.icon_cache[url]

        cache_file = self._cache_file(url)
        pixmap = QPixmap()
        if cache_file.exists() and pixmap.load(str(cache_file)):
            self.icon_cache[url] = pixmap
            return pixmap

        for icon_url in self._build_icon_candidates(url):
            try:
                request = urllib.request.Request(icon_url, headers={"User-Agent": "Mozilla/5.0"})
                with urllib.request.urlopen(request, timeout=3) as response:
                    raw = response.read()
                if pixmap.loadFromData(raw):
                    pixmap.save(str(cache_file), "PNG")
                    self.icon_cache[url] = pixmap
                    return pixmap
            except Exception:
                continue

        return None
