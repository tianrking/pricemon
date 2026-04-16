"""Alibaba.com 抓取器"""

from __future__ import annotations

import logging
import re
import time

from .base import BaseScraper
from ..browser import Browser
from ..config import PAGE_LOAD_WAIT, DETAIL_WAIT, DEFAULT_TIMEOUT
from ..models import Product

logger = logging.getLogger("pricemon")

# 搜索页产品卡片 CSS 选择器
_CARD_SELECTOR = (
    ".searchx-offer-item, .organic-gallery-offer__outter, .fy23-search-card"
)

# 搜索页 JS 提取脚本
_EXTRACT_JS = f"""
const cards = document.querySelectorAll('{_CARD_SELECTOR}');
const results = [];
cards.forEach(card => {{
    const t = card.querySelector('[class*="title"]') || card.querySelector('h2');
    const l = card.querySelector('a');
    const p = card.querySelector('[class*="price"]');
    const s = card.querySelector('[class*="seller"]') || card.querySelector('[class*="company"]');
    const i = card.querySelector('img');
    if (t && t.textContent.trim()) {{
        results.push({{
            title: t.textContent.trim(),
            url: l ? l.href.split('?')[0] : '',
            price_text: p ? p.textContent.trim() : '',
            supplier: s ? s.textContent.trim() : '',
            image: i ? i.src : '',
        }});
    }}
}});
return JSON.stringify(results);
"""

# Alibaba 特有的验证码信号
_CAPTCHA_SIGNALS = ("baxia-punish", "captcha-intercept", "nocaptcha")


class AlibabaScraper(BaseScraper):
    """Alibaba.com 产品抓取器"""

    name = "alibaba"
    domain = ".alibaba.com"
    site_url = "https://www.alibaba.com"

    _search_url = "https://www.alibaba.com/trade/search"

    def __init__(self, browser: Browser):
        super().__init__(browser)

    def search(self, keyword: str, page: int = 1) -> list[Product]:
        url = (
            f"{self._search_url}?"
            f"SearchText={keyword.replace(' ', '+')}"
            f"&page={page}&viewtype=G"
        )
        logger.info("访问: %s", url)
        self.browser.page.get(url)
        time.sleep(PAGE_LOAD_WAIT)
        self.browser.page.wait.doc_loaded(timeout=DEFAULT_TIMEOUT)
        self.browser.scroll_to_bottom()

        if self.browser.has_captcha(_CAPTCHA_SIGNALS):
            logger.warning("遇到验证码，Cookie 可能已过期")
            return []

        raw = self.browser.extract_js(_EXTRACT_JS)
        products = [self._to_product(item) for item in raw]
        logger.info("提取到 %d 个产品", len(products))
        return products

    def fetch_detail(self, product_url: str) -> dict:
        if not product_url or "alibaba.com" not in product_url:
            return {}
        try:
            self.browser.page.get(product_url)
            time.sleep(DETAIL_WAIT)
            detail: dict = {}

            price_el = (
                self.browser.page.ele("css:.price", timeout=3)
                or self.browser.page.ele("css:.pre-inquiry-price", timeout=3)
            )
            if price_el:
                detail["detail_price"] = price_el.text.strip()

            specs = self._extract_specs()
            if specs:
                detail["specifications"] = specs

            company_el = self.browser.page.ele("css:.company-name", timeout=2)
            if company_el:
                detail["company"] = company_el.text.strip()

            return detail
        except Exception as exc:
            logger.debug("详情获取失败: %s", exc)
            return {}

    # -- 内部方法 --

    @staticmethod
    def _to_product(item: dict) -> Product:
        p = Product(
            title=item.get("title", ""),
            url=item.get("url", ""),
            price_text=item.get("price_text", ""),
            supplier=item.get("supplier", ""),
            image=item.get("image", ""),
        )
        if p.price_text:
            nums = re.findall(r"[\d.,]+", p.price_text)
            if nums:
                p.price_value = nums[0].replace(",", "")
        return p

    def _extract_specs(self) -> dict:
        specs: dict = {}
        rows = (
            self.browser.page.eles("css:.do-entry-item", timeout=2)
            or self.browser.page.eles("css:.attribute-item", timeout=2)
        )
        for row in rows:
            try:
                lbl = row.ele("css:.do-entry-item-label", timeout=0.5)
                val = row.ele("css:.do-entry-item-value", timeout=0.5)
                if lbl and val:
                    specs[lbl.text.strip()] = val.text.strip()
            except Exception:
                continue
        return specs
