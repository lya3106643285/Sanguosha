"""Convert the captured GitBook rule pages to Markdown."""

from __future__ import annotations

import os
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

from bs4 import BeautifulSoup
from markdownify import MarkdownConverter


ROOT = Path(__file__).resolve().parents[1]
HTML_ROOT = ROOT / "source" / "original_rules" / "html"
MD_ROOT = ROOT / "source" / "original_rules" / "md"


class RuleConverter(MarkdownConverter):
    def escape(self, text: str, parent_tags: set[str]) -> str:
        # A literal > at the beginning of a line is otherwise parsed as a quote.
        return super().escape(text, parent_tags).replace(">", r"\>")


def convert_page(source: Path) -> None:
    soup = BeautifulSoup(source.read_text(encoding="utf-8"), "html.parser")
    content = soup.select_one(".page-inner .normal")
    if content is None:
        raise ValueError(f"No rule content found in {source}")
    output = MD_ROOT / source.relative_to(HTML_ROOT).with_suffix(".md")
    for tag, attribute in (("a", "href"), ("img", "src")):
        for element in content.find_all(tag):
            value = element.get(attribute)
            if not value:
                continue
            parts = urlsplit(value)
            if parts.scheme or parts.netloc or value.startswith("#"):
                continue
            target = (source.parent / parts.path.replace("\\", "/")).resolve()
            if tag == "a" and target.suffix.lower() == ".html" and target.is_file():
                target = MD_ROOT / target.relative_to(HTML_ROOT).with_suffix(".md")
            relative = os.path.relpath(target, output.parent)
            element[attribute] = urlunsplit(("", "", relative, parts.query, parts.fragment))
    title = soup.title.get_text(" ", strip=True).split(" | ")[0] if soup.title else ""
    converter = RuleConverter(
        heading_style="ATX",
        bullets="-",
        strip=["script", "style"],
    )
    markdown = converter.convert_soup(content).strip()
    if not markdown.startswith("#") and title:
        markdown = f"# {title}\n\n{markdown}"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(markdown + "\n", encoding="utf-8")


def main() -> None:
    pages = sorted(HTML_ROOT.rglob("*.html"))
    for page in pages:
        convert_page(page)
    print(f"Converted {len(pages)} pages into {MD_ROOT.relative_to(ROOT)}/")


if __name__ == "__main__":
    main()
