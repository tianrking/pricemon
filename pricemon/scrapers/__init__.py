"""抓取器注册表

用法:
    from pricemon.scrapers import get_scraper, list_scrapers

    ScraperClass = get_scraper("alibaba")
    scraper = ScraperClass(browser)

添加新网站:
    1. 在 scrapers/ 下创建新文件 (如 amazon.py)
    2. 继承 BaseScraper 实现 search() 和 fetch_detail()
    3. 在下方 _register() 中注册
"""

from __future__ import annotations

from typing import Type

from .base import BaseScraper
from .alibaba import AlibabaScraper
from .amazon import AmazonScraper

# 注册表: name -> class
_REGISTRY: dict[str, Type[BaseScraper]] = {}


def _register(*scrapers: Type[BaseScraper]):
    for cls in scrapers:
        _REGISTRY[cls.name] = cls


def get_scraper(name: str) -> Type[BaseScraper]:
    """按名称获取抓取器类"""
    if name not in _REGISTRY:
        available = ", ".join(_REGISTRY) or "无"
        raise ValueError(f"未知网站 '{name}'，可用: {available}")
    return _REGISTRY[name]


def list_scrapers() -> list[str]:
    """列出所有已注册的网站"""
    return list(_REGISTRY.keys())


# 注册内置抓取器
_register(AlibabaScraper, AmazonScraper)
