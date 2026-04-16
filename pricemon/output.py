"""终端输出格式化"""

from .config import SUMMARY_LIMIT
from .models import ScrapeResult


def print_summary(result: ScrapeResult):
    products = result.products
    if not products:
        print("\n未抓取到数据。Cookie 可能已过期，请重新获取。")
        return

    print(f"\n{'=' * 60}")
    print(f"共 {result.total} 个产品")
    print(f"{'=' * 60}")

    for i, p in enumerate(products[:SUMMARY_LIMIT], 1):
        print(f"\n[{i}] {p.title[:60]}")
        print(f"    价格: {p.price_text or 'N/A'}")
        if p.supplier:
            print(f"    供应商: {p.supplier}")
        if p.price_changed:
            print(f"    ** 变动: {p.price_change}")

    remaining = result.total - SUMMARY_LIMIT
    if remaining > 0:
        print(f"\n... 还有 {remaining} 个产品")
