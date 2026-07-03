from __future__ import annotations

from html.parser import HTMLParser
from typing import Any
import re


class _KeyValueHTMLParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self._stack: list[str] = []
        self.lines: list[str] = []
        self.current_text: list[str] = []

    def handle_starttag(self, tag: str, attrs):
        self._stack.append(tag)
        if tag in {"br", "p", "div", "li", "tr"}:
            self.lines.append("\n")

    def handle_endtag(self, tag: str):
        if tag in self._stack:
            while self._stack:
                popped = self._stack.pop()
                if popped == tag:
                    break
        if tag in {"p", "div", "li", "tr"}:
            self.lines.append("\n")

    def handle_data(self, data: str):
        text = data.strip()
        if text:
            self.lines.append(text)


class DescriptionParser:
    """Transforme une description HTML en dictionnaire clé/valeur."""

    def parse(self, description_html: str | None) -> dict[str, str]:
        if not description_html:
            return {}

        text = self._html_to_text(description_html)
        result: dict[str, str] = {}
        for line in [chunk.strip() for chunk in text.splitlines() if chunk.strip()]:
            if ":" in line:
                key, value = line.split(":", 1)
                key = self._normalize_key(key)
                value = value.strip()
                if key:
                    result[key] = value
            elif "=" in line:
                key, value = line.split("=", 1)
                key = self._normalize_key(key)
                value = value.strip()
                if key:
                    result[key] = value
        return result

    def _html_to_text(self, description_html: str) -> str:
        parser = _KeyValueHTMLParser()
        parser.feed(description_html)
        raw_text = " ".join(parser.lines)
        raw_text = re.sub(r"\s+", " ", raw_text)
        raw_text = raw_text.replace(" \n ", "\n")
        return raw_text.replace("\n ", "\n").replace(" \n", "\n")

    def _normalize_key(self, key: str) -> str:
        normalized = re.sub(r"\s+", " ", key).strip().lower()
        normalized = normalized.replace("é", "e").replace("è", "e").replace("à", "a")
        return normalized
