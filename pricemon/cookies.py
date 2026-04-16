"""Cookie 加载，支持多种格式"""

from __future__ import annotations

import json
from pathlib import Path


class CookieLoader:
    """从文件加载 cookies，自动识别 JSON / Netscape / 原始字符串三种格式"""

    def __init__(self, domain: str = ".alibaba.com"):
        self.domain = domain

    def load(self, filepath: str) -> list[dict]:
        text = Path(filepath).read_text(encoding="utf-8").strip()
        for parser in (self._parse_json, self._parse_netscape, self._parse_raw):
            result = parser(text)
            if result:
                return result
        return []

    # -- 格式解析 --

    def _parse_json(self, text: str) -> list[dict] | None:
        try:
            data = json.loads(text)
            return data if isinstance(data, list) else None
        except (json.JSONDecodeError, ValueError):
            return None

    def _parse_netscape(self, text: str) -> list[dict] | None:
        if "\t" not in text:
            return None
        cookies = []
        for line in text.split("\n"):
            parts = line.strip().split("\t")
            if len(parts) >= 7 and not parts[0].startswith("#"):
                cookies.append({
                    "domain": parts[0], "path": parts[2],
                    "name": parts[5], "value": parts[6],
                })
        return cookies or None

    def _parse_raw(self, text: str) -> list[dict]:
        cookies = []
        for item in text.split(";"):
            item = item.strip()
            if "=" in item:
                k, v = item.split("=", 1)
                cookies.append({
                    "name": k.strip(), "value": v.strip(),
                    "domain": self.domain, "path": "/",
                })
        return cookies
