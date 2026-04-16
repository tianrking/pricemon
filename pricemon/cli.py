"""CLI 入口与主流程"""

from __future__ import annotations

import argparse
import logging
import sys
import time

from .config import VERSION, DEFAULT_KEYWORD, DEFAULT_SITE, RETRY_WAIT, RESULTS_DIR
from .cookies import CookieLoader
from .browser import Browser
from .scrapers import get_scraper
from .store import ResultStore, PriceComparator
from .output import print_summary
from .models import ScrapeResult

logger = logging.getLogger("pricemon")


def build_parser() -> argparse.ArgumentParser:
    return argparse.ArgumentParser(
        prog="pricemon",
        description="pricemon - 通用价格监控工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
获取 Cookie:
  1. 浏览器打开目标网站并登录
  2. F12 → Console → 输入 document.cookie 回车
  3. 复制输出保存到 cookies.txt
  4. python pricemon.py -c cookies.txt -k "关键词"

示例:
  python pricemon.py -c cookies.txt -k "DM4340 servo motor"
  python pricemon.py -c cookies.txt --headless -k "brushless motor" -p 3
  python pricemon.py -c cookies.txt -k "servo motor" --compare results/
        """,
    )


def _add_arguments(parser: argparse.ArgumentParser):
    parser.add_argument("-c", "--cookie-file", help="Cookie 文件路径")
    parser.add_argument("-k", "--keyword", default=DEFAULT_KEYWORD, help="搜索关键词")
    parser.add_argument("-p", "--pages", type=int, default=1, help="抓取页数")
    parser.add_argument(
        "--site", default=DEFAULT_SITE,
        help=f"目标网站 (默认 {DEFAULT_SITE})",
    )
    parser.add_argument("--headless", action="store_true", help="无头模式")
    parser.add_argument("--details", action="store_true", help="获取详情页规格")
    parser.add_argument("--compare", metavar="DIR", help="历史数据目录对比")
    parser.add_argument("-v", "--verbose", action="store_true", help="详细日志")
    parser.add_argument("--version", action="version", version=f"%(prog)s {VERSION}")


def _setup_logging(verbose: bool):
    level = logging.DEBUG if verbose else logging.INFO
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter("%(message)s"))
    logger.setLevel(level)
    logger.addHandler(handler)


def main(argv: list[str] | None = None):
    parser = build_parser()
    _add_arguments(parser)
    args = parser.parse_args(argv)

    _setup_logging(args.verbose)

    # 获取抓取器
    scraper_cls = get_scraper(args.site)

    print(f"pricemon v{VERSION}")
    print(f"  网站:   {args.site}")
    print(f"  关键词: {args.keyword}")
    print(f"  Cookie: {args.cookie_file or '匿名访问'}")
    print(f"  页数:   {args.pages}\n")

    # 初始化组件
    browser = Browser(headless=args.headless)
    scraper = scraper_cls(browser)
    store = ResultStore()
    result = ScrapeResult(keyword=args.keyword, pages=args.pages, site=args.site)

    # 加载 cookies
    cookies: list[dict] = []
    if args.cookie_file:
        cookies = CookieLoader(domain=scraper.domain).load(args.cookie_file)
        logger.info("加载 cookies: %d 条", len(cookies))

    try:
        if cookies:
            browser.inject_cookies(cookies, site=scraper.site_url)

        # 逐页抓取
        for pg in range(1, args.pages + 1):
            logger.info("\n[第 %d/%d 页]", pg, args.pages)
            products = scraper.search(args.keyword, page=pg)

            if not products and pg == 1:
                logger.info("  重试...")
                time.sleep(RETRY_WAIT)
                products = scraper.search(args.keyword, page=pg)

            result.products.extend(products)

            if pg < args.pages:
                time.sleep(2)

        # 获取详情
        if args.details and result.products:
            logger.info("\n获取产品详情...")
            for i, p in enumerate(result.products):
                if p.url:
                    logger.info("  [%d/%d] %s...", i + 1, result.total, p.title[:40])
                    detail = scraper.fetch_detail(p.url)
                    for k, v in detail.items():
                        setattr(p, k, v)
                    time.sleep(1)

        # 价格对比
        if args.compare:
            result.products = PriceComparator(args.compare).compare(result.products)

        # 保存并输出摘要
        path = store.save(result)
        logger.info("\n已保存: %s", path)
        print_summary(result)

    except KeyboardInterrupt:
        logger.info("\n\n中断，保存已抓取数据...")
        if result.products:
            store.save(result)

    except Exception as exc:
        logger.error("\n错误: %s", exc)
        if result.products:
            store.save(result)

    finally:
        browser.close()
        logger.info("\n完成。")
