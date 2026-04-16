"""抓取器抽象基类"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..browser import Browser
    from ..models import Product


class BaseScraper(ABC):
    """所有网站抓取器的基类

    子类必须实现:
        - name: 网站标识 (如 "alibaba", "amazon")
        - domain: cookie 域名 (如 ".alibaba.com")
        - site_url: 网站首页 (用于 cookie 注入)
        - search(): 搜索产品
        - fetch_detail(): 获取产品详情
    """

    name: str = ""
    domain: str = ""
    site_url: str = ""

    def __init__(self, browser: Browser):
        self.browser = browser

    @abstractmethod
    def search(self, keyword: str, page: int = 1) -> list[Product]:
        """搜索产品，返回产品列表"""

    @abstractmethod
    def fetch_detail(self, product_url: str) -> dict:
        """获取产品详情页数据"""
