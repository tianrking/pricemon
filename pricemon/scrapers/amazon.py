"""Amazon.com 产品抓取器"""

from __future__ import annotations

import json
import logging
import re

from .base import BaseScraper
from ..models import Product

logger = logging.getLogger("pricemon")

# Amazon 搜索页提取 JS
AMAZON_EXTRACT_JS = """
const cards = document.querySelectorAll(
    '[data-component-type="s-search-result"], .s-result-item'
);
const results = [];
cards.forEach(card => {
    const titleEl = card.querySelector('h2 a span') || card.querySelector('h2 span');
    const linkEl = card.querySelector('h2 a') || card.querySelector('a.a-link-normal');
    const priceWhole = card.querySelector('.a-price .a-price-whole');
    const priceFraction = card.querySelector('.a-price .a-price-fraction');
    const priceSymbol = card.querySelector('.a-price .a-price-symbol');
    const ratingEl = card.querySelector('.a-icon-star-small .a-icon-alt') ||
                     card.querySelector('[aria-label*="out of"]');
    const reviewEl = card.querySelector('.a-size-small .a-link-normal .a-size-base');
    const imgEl = card.querySelector('.s-image');
    const primeEl = card.querySelector('.a-icon-prime');

    if (titleEl && titleEl.textContent.trim()) {
        let price = '';
        if (priceWhole) {
            price = (priceSymbol ? priceSymbol.textContent.trim() : '$') +
                    priceWhole.textContent.trim().replace(/\\n/g, '');
            if (priceFraction) price += '.' + priceFraction.textContent.trim();
        }
        results.push({
            title: titleEl.textContent.trim(),
            url: linkEl ? linkEl.href.split('?')[0] : '',
            price_text: price,
            rating: ratingEl ? ratingEl.getAttribute('aria-label') || ratingEl.textContent.trim() : '',
            reviews: reviewEl ? reviewEl.textContent.trim() : '',
            image: imgEl ? imgEl.src : '',
            prime: primeEl ? 'yes' : '',
        });
    }
});
return JSON.stringify(results);
"""


class AmazonScraper(BaseScraper):
    """Amazon.com 产品抓取器"""

    name = "amazon"
    domain = ".amazon.com"
    site_url = "https://www.amazon.com"

    # Amazon 特有验证码信号
    _captcha_signals = (
        "api-services-support@amazon.com",
        "enter the characters you see below",
        "sorry! something went wrong",
        "type the characters you see",
    )

    def search(self, keyword: str, page: int = 1) -> list[Product]:
        url = (
            f"https://www.amazon.com/s?"
            f"k={keyword.replace(' ', '+')}"
            f"&page={page}"
            f"&ref=cs_503_search"
        )
        logger.info("访问: %s", url)
        self.browser.page.get(url)

        import time
        from ..config import PAGE_LOAD_WAIT, DEFAULT_TIMEOUT
        time.sleep(PAGE_LOAD_WAIT)
        self.browser.page.wait.doc_loaded(timeout=DEFAULT_TIMEOUT)

        # Amazon 检测验证码，重试一次
        if self.browser.has_captcha(signals=self._captcha_signals):
            logger.warning("触发验证码，等待重试...")
            time.sleep(3)
            self.browser.page.get(url)
            time.sleep(PAGE_LOAD_WAIT)
            self.browser.page.wait.doc_loaded(timeout=DEFAULT_TIMEOUT)

        self.browser.scroll_to_bottom()

        # 检测 Amazon 验证码
        if self.browser.has_captcha(signals=self._captcha_signals):
            logger.warning("遇到 Amazon 验证码，Cookie 可能已过期")
            return []

        raw = self.browser.extract_js(AMAZON_EXTRACT_JS)
        products = [self._to_product(item) for item in raw]
        logger.info("提取到 %d 个产品", len(products))
        return products

    def fetch_detail(self, product_url: str) -> dict:
        if not product_url or "amazon" not in product_url:
            return {}
        try:
            self.browser.page.get(product_url)

            import time
            from ..config import DETAIL_WAIT
            time.sleep(DETAIL_WAIT)

            detail = {}

            # 价格
            price_el = (
                self.browser.page.ele("css:#priceblock_ourprice", timeout=2)
                or self.browser.page.ele("css:#priceblock_dealprice", timeout=2)
                or self.browser.page.ele("css:.a-price .a-offscreen", timeout=2)
            )
            if price_el:
                detail["detail_price"] = price_el.text.strip()

            # 技术规格
            specs = {}
            rows = self.browser.page.eles("css:#productDetails_techSpec_section_1 tr", timeout=2)
            if not rows:
                rows = self.browser.page.eles("css:#tech-spec-table tr", timeout=2)
            for row in rows:
                try:
                    th = row.ele("tag:th", timeout=0.5)
                    td = row.ele("tag:td", timeout=0.5)
                    if th and td:
                        specs[th.text.strip()] = td.text.strip()
                except Exception:
                    continue
            if specs:
                detail["specifications"] = specs

            # 品牌
            brand_el = (
                self.browser.page.ele("css:#bylineInfo", timeout=2)
                or self.browser.page.ele("css:a#bylineInfo", timeout=2)
            )
            if brand_el:
                detail["brand"] = brand_el.text.strip()

            # 评分
            rating_el = self.browser.page.ele("css:#acrPopover span.a-icon-alt", timeout=2)
            if rating_el:
                detail["rating"] = rating_el.text.strip()

            return detail
        except Exception as exc:
            logger.debug("详情获取失败: %s", exc)
            return {}

    @staticmethod
    def _to_product(item: dict) -> Product:
        p = Product(
            title=item.get("title", ""),
            url=item.get("url", ""),
            price_text=item.get("price_text", ""),
            supplier=item.get("brand", ""),
            image=item.get("image", ""),
        )
        # Amazon 额外字段
        if item.get("rating"):
            p.moq = item["rating"]  # 复用 moq 字段存评分
        if p.price_text:
            nums = re.findall(r"[\d.,]+", p.price_text)
            if nums:
                p.price_value = nums[0].replace(",", "")
        return p
