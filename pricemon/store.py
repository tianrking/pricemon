"""结果存储与价格对比"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from .config import RESULTS_DIR
from .models import Product, ScrapeResult


class ResultStore:
    """保存抓取结果到 JSON 文件"""

    def __init__(self, output_dir: str = RESULTS_DIR):
        self.output_dir = Path(output_dir)

    def save(self, result: ScrapeResult) -> Path:
        self.output_dir.mkdir(parents=True, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        slug = result.keyword.replace(" ", "_")
        prefix = f"{result.site}_" if result.site else ""
        path = self.output_dir / f"{prefix}{slug}_{ts}.json"

        with open(path, "w", encoding="utf-8") as f:
            json.dump(result.to_dict(), f, ensure_ascii=False, indent=2)

        return path


class PriceComparator:
    """与历史数据对比价格变化"""

    def __init__(self, history_dir: str):
        self.history_dir = Path(history_dir)

    def compare(self, products: list[Product]) -> list[Product]:
        baseline = self._load_baseline()
        if not baseline:
            return products

        for product in products:
            key = product.title[:50]
            old_price = baseline.get(key)
            if old_price and old_price != product.price_text:
                product.price_changed = True
                product.price_change = f"{old_price} -> {product.price_text}"

        return products

    def _load_baseline(self) -> dict[str, str]:
        files = sorted(self.history_dir.glob("*.json"))
        if not files:
            return {}
        with open(files[-1], encoding="utf-8") as f:
            data = json.load(f)
        return {
            p.get("title", "")[:50]: p.get("price_text", "")
            for p in data.get("products", [])
        }
