"""Chromium 浏览器封装"""

from __future__ import annotations

import json
import logging
import time

from DrissionPage import ChromiumPage, ChromiumOptions

from .config import (
    DEFAULT_TIMEOUT, SCROLL_ROUNDS, SCROLL_PAUSE, CAPTCHA_SIGNALS,
)

logger = logging.getLogger("pricemon")


class Browser:
    """Chromium 浏览器封装，提供 Cookie 注入、滚动、验证码检测等通用能力"""

    def __init__(self, headless: bool = False, timeout: int = DEFAULT_TIMEOUT):
        opts = ChromiumOptions()
        if headless:
            opts.headless()
        for arg in (
            "--no-sandbox", "--disable-gpu",
            "--window-size=1920,1080", "--lang=en-US",
            "--disable-blink-features=AutomationControlled",
        ):
            opts.set_argument(arg)
        opts.set_user_agent(
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
        )
        self._page = ChromiumPage(opts)
        self._page.set.timeouts(base=timeout)

    @property
    def page(self) -> ChromiumPage:
        return self._page

    def inject_cookies(self, cookies: list[dict], site: str):
        """先访问 site 建立域，再逐条注入 cookies"""
        self._page.get(site)
        time.sleep(1)
        loaded = sum(1 for c in cookies if self._safe_set_cookie(c))
        logger.info("注入 cookies: %d/%d 条", loaded, len(cookies))
        return loaded

    def scroll_to_bottom(self, rounds: int = SCROLL_ROUNDS, pause: float = SCROLL_PAUSE):
        for _ in range(rounds):
            self._page.run_js("window.scrollTo(0, document.body.scrollHeight)")
            time.sleep(pause)

    def has_captcha(self, signals: tuple[str, ...] = CAPTCHA_SIGNALS) -> bool:
        html = (self._page.html or "").lower()
        return any(s in html for s in signals)

    def extract_js(self, js: str, timeout: int = 10) -> list[dict]:
        """执行 JS 并解析返回的 JSON 数组"""
        raw = self._page.run_js(js, timeout=timeout)
        if raw:
            return json.loads(raw)
        return []

    def close(self):
        self._page.quit()

    def _safe_set_cookie(self, cookie: dict) -> bool:
        try:
            self._page.set.cookies(cookie)
            return True
        except Exception:
            return False
