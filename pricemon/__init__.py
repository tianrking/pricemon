"""pricemon - 通用价格监控工具

用法:
    python -m pricemon -c cookies.txt -k "关键词"
"""

from .config import VERSION
from .models import Product, ScrapeResult
from .scrapers import get_scraper, list_scrapers

__version__ = VERSION
__all__ = [
    "VERSION",
    "Product",
    "ScrapeResult",
    "get_scraper",
    "list_scrapers",
]
