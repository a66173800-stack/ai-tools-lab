#!/usr/bin/env python3
"""Export the BEAUTY EDIT subtree as an independently deployable GitHub Pages site.

Run from repository root:
  python3 scripts/export_beauty_site.py

No external dependencies or credentials are needed. This NEVER edits the live
site, the source repository CNAME, or DNS records.
"""
from __future__ import annotations

import argparse
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit
from shutil import copytree, rmtree
from zipfile import ZipFile, ZIP_DEFLATED

SOURCE_CANONICAL = "https://a66173800-stack.github.io/ai-tools-lab/yorisuguri/beauty/"
DEFAULT_DOMAIN = "beauty.yorisuguri-note.com"
ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "yorisuguri" / "beauty"
OUTPUT = ROOT / "dist" / "beauty-site-ready"
ARCHIVE = ROOT / "dist" / "beauty-site-ready.zip"

class LocalLinks(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        for key, val in attrs:
            if val and key in ("href", "src"):
                self.links.append(val)

def check_links(site: Path) -> list[str]:
    errors: list[str] = []
    for doc in site.rglob("*.html"):
        parser = LocalLinks()
        parser.feed(doc.read_text(encoding="utf-8"))
        for link in parser.links:
            url = urlsplit(link)
            if url.scheme or url.netloc or link.startswith("#") or link.startswith("data:"):
                continue
            rel = unquote(url.path)
            if not rel:
                continue
            target = (site / rel.lstrip("/")) if rel.startswith("/") else (doc.parent / rel)
            if rel.endswith("/"):
                target = target / "index.html"
            if not target.exists():
                errors.append(f"{doc.relative_to(site)} -> {link}")
    return errors

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--domain", default=DEFAULT_DOMAIN,
                        help="Final host only, e.g. beauty.example.com")
    args = parser.parse_args()
    host = args.domain.strip().lower()
    if not host or "/" in host or ":" in host or " " in host:
        parser.error("--domain must be a bare hostname")
    if not (SOURCE / "index.html").exists():
        raise SystemExit(f"Source beauty site not found: {SOURCE}")
    if OUTPUT.exists():
        rmtree(OUTPUT)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    copytree(SOURCE, OUTPUT)
    destination = f"https://{host}/"

    # Canonicals, OG URL and sitemap locations must point to the new domain.
    for path in list(OUTPUT.rglob("*.html")) + list(OUTPUT.rglob("*.xml")):
        content = path.read_text(encoding="utf-8")
        path.write_text(content.replace(SOURCE_CANONICAL, destination),
                        encoding="utf-8")

    # Only the exported *independent repository* should contain these.
    (OUTPUT / "CNAME").write_text(host + "\n", encoding="utf-8")
    (OUTPUT / "robots.txt").write_text(
        f"User-agent: *\nAllow: /\nSitemap: {destination}sitemap.xml\n",
        encoding="utf-8")
    (OUTPUT / ".nojekyll").write_text("", encoding="utf-8")
    (OUTPUT / "404.html").write_text(
        '<!doctype html><html lang="ja"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        '<title>ページが見つかりません｜BEAUTY EDIT</title>'
        '<link rel="stylesheet" href="/assets/beauty.css"></head>'
        '<body><main style="max-width:720px;margin:13vh auto;padding:30px">'
        '<p>404 / PAGE NOT FOUND</p><h1>ページが見つかりません</h1>'
        '<p>URLが変更されたか、ページが移動した可能性があります。</p>'
        '<a href="/" class="button">美容サイトのトップへ戻る →</a>'
        '</main></body></html>',
        encoding="utf-8")
    (OUTPUT / "README.md").write_text(
        "# ヨリスグリノート BEAUTY EDIT\n\n"
        "このフォルダは独立公開用に書き出した美容サイトです。"
        "トップ、8カテゴリ・18記事、ネイルサロン特集、CSS、"
        "サイトマップを含みます。\n\n"
        "## 独自ドメイン接続\n"
        "1. GitHubで Public リポジトリ `yorisuguri-beauty` を作る。\n"
        "2. ZIPの**中身**をリポジトリのルートに追加する。\n"
        "3. Settings > Pages > Deploy from a branch > main / (root) を選ぶ。\n"
        f"4. Pages の Custom domain を `{host}` にする。\n"
        "5. DNSに `beauty` の CNAME を追加・更新し、"
        "`a66173800-stack.github.io` に向ける。"
        "競合する旧レコードがあればDNS管理側で確認する。\n"
        "6. GitHub Pages のDNSチェック後に Enforce HTTPS を有効にし、"
        "実際にトップ・記事・特集へのアクセスを確認する。\n\n"
        "**注意:** 元の `ai-tools-lab` のルートの `CNAME`"
        " は変えない。美容以外のサイトに影響させないためです。\n",
        encoding="utf-8")

    issues = check_links(OUTPUT)
    html_count = len(list(OUTPUT.rglob("*.html")))
    article_count = len(list((OUTPUT / "articles").glob("*.html")))
    if issues:
        raise SystemExit("Broken internal links in export:\n" + "\n".join(issues))
    if article_count != 18:
        raise SystemExit(f"Expected 18 article pages; found {article_count}")

    if ARCHIVE.exists():
        ARCHIVE.unlink()
    with ZipFile(ARCHIVE, "w", ZIP_DEFLATED) as archive:
        for item in sorted(OUTPUT.rglob("*")):
            if item.is_file():
                archive.write(item, item.relative_to(OUTPUT).as_posix())
    print(f"Export complete: {ARCHIVE} ({html_count} HTML pages, {article_count} topics)")
    print(f"Canonical host: {destination}")
    print("Internal link validation: passed")

if __name__ == "__main__":
    main()
