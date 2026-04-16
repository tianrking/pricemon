"""数据模型"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import datetime


@dataclass
class Product:
    """单个产品信息"""
    title: str = ""
    url: str = ""
    price_text: str = ""
    price_value: str = ""
    supplier: str = ""
    image: str = ""
    moq: str = ""
    # 详情页字段
    detail_price: str = ""
    specifications: dict = field(default_factory=dict)
    company: str = ""
    # 对比字段
    price_change: str = ""
    price_changed: bool = False

    def to_dict(self) -> dict:
        return {k: v for k, v in asdict(self).items() if v}


@dataclass
class ScrapeResult:
    """一次抓取的结果"""
    keyword: str
    pages: int
    site: str = ""
    products: list[Product] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    @property
    def total(self) -> int:
        return len(self.products)

    def to_dict(self) -> dict:
        d = {
            "keyword": self.keyword,
            "pages": self.pages,
            "total_products": self.total,
            "timestamp": self.timestamp,
            "products": [p.to_dict() for p in self.products],
        }
        if self.site:
            d["site"] = self.site
        return d
