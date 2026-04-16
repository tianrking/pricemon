# pricemon

通用价格监控工具 — 基于 DrissionPage 的多网站产品价格抓取。

当前支持 **Alibaba.com** 和 **Amazon.com**，架构可扩展其他网站。

## 前置依赖

- **Python 3.8+**
- **Chrome / Chromium** 浏览器
- **DrissionPage**（随 pricemon 自动安装，也可手动安装：`uv pip install DrissionPage`）

## 安装

### 使用 uv（推荐）

```bash
uv pip install pricemon
```

或从源码安装：

```bash
git clone https://github.com/tianrking/pricemon.git
cd pricemon
uv pip install -e .
```

### 使用 pip

```bash
pip install pricemon
```

### 直接运行

```bash
git clone https://github.com/tianrking/pricemon.git
cd pricemon
uv run python pricemon.py -c cookies.txt -k "关键词"
```

## 快速开始

### 1. 运行抓取

```bash
# Alibaba（默认），带 Cookie
pricemon -c cookies.txt -k "DM4340 servo motor"

# Amazon
pricemon --site amazon -k "servo motor"

# 无头模式
pricemon -c cookies.txt --headless -k "brushless motor"

# 多页抓取
pricemon -c cookies.txt -k "servo motor" -p 5

# 获取详情页规格
pricemon -c cookies.txt --details -k "DM4340"

# 价格对比
pricemon -c cookies.txt -k "servo motor" --compare results/
```

不提供 Cookie 也可以运行，但部分网站可能会弹出验证码，需要手动通过一次。

### 2. 获取 Cookie（可选但推荐）

提供 Cookie 可以大幅提高成功率，避免验证码拦截。

1. 用浏览器打开目标网站并登录
2. 按 `F12` → **Console** → 输入 `document.cookie` 回车
3. 复制输出的字符串，保存到文件 `cookies.txt`

也可用浏览器扩展 [Cookie-Editor](https://chrome.google.com/webstore/detail/cookie-editor/hlkenndednhfkekhgcdicdfddnkalmdm) 导出 JSON 格式。

## 参数说明

| 参数 | 说明 | 示例 |
|------|------|------|
| `-c` / `--cookie-file` | Cookie 文件路径（可选） | `-c cookies.txt` |
| `-k` / `--keyword` | 搜索关键词（默认 "DM motor servo"） | `-k "brushless DC motor"` |
| `-p` / `--pages` | 抓取页数（默认 1） | `-p 3` |
| `--site` | 目标网站，支持 alibaba / amazon（默认 alibaba） | `--site amazon` |
| `--headless` | 无头模式，不显示浏览器 | |
| `--details` | 获取产品详情页规格参数 | |
| `--compare` | 历史数据目录，对比价格变化 | `--compare results/` |
| `-v` / `--verbose` | 详细日志 | |

## Cookie 文件格式

自动识别三种格式：

**格式一：原始字符串**（`document.cookie` 输出）
```
_m_h5_tk=abc123; cookie2=xyz789; _tb_token_=token123
```

**格式二：JSON 数组**（Cookie-Editor 导出）
```json
[{"name": "_m_h5_tk", "value": "abc123", "domain": ".alibaba.com", "path": "/"}]
```

**格式三：Netscape 格式**（wget/curl 导出）
```
.alibaba.com	TRUE	/	FALSE	0	_m_h5_tk	abc123
```

## 输出格式

结果保存到 `results/` 目录：

```json
{
  "keyword": "servo motor",
  "site": "alibaba",
  "pages": 1,
  "total_products": 48,
  "timestamp": "2026-04-16T15:14:59",
  "products": [
    {
      "title": "DM4340P Brushless Servo Motor...",
      "url": "https://www.alibaba.com/product-detail/...",
      "price_text": "27,099-33,513",
      "supplier": "Shenzhen Komo Innovation Robotics Technology Co., Ltd.",
      "image": "https://s.alicdn.com/@sc04/..."
    }
  ]
}
```

## 价格对比

```bash
pricemon -c cookies.txt -k "DM4340 motor" -p 1
# 几天后再运行
pricemon -c cookies.txt -k "DM4340 motor" -p 1 --compare results/
```

变动的产品标记 `"price_changed": true`。

## 抓取能力

### Alibaba.com

| 页数 | 产品数 | 耗时 |
|------|--------|------|
| 1 页 | 48 个 | ~15秒 |
| 3 页 | 144 个 | ~40秒 |
| 10 页 | 480 个 | ~2分钟 |
| 50 页 | 2,400 个 | ~8分钟 |

### Amazon.com

| 页数 | 产品数 | 耗时 |
|------|--------|------|
| 1 页 | 50 个 | ~15秒 |
| 3 页 | 150 个 | ~40秒 |
| 10 页 | 500 个 | ~2分钟 |

## 扩展新网站

在 `pricemon/scrapers/` 下新建文件：

```python
# pricemon/scrapers/ebay.py
from .base import BaseScraper
from ..models import Product

class EbayScraper(BaseScraper):
    name = "ebay"
    domain = ".ebay.com"
    site_url = "https://www.ebay.com"

    def search(self, keyword, page=1) -> list[Product]:
        ...

    def fetch_detail(self, product_url) -> dict:
        ...
```

在 `scrapers/__init__.py` 注册：

```python
_register(AlibabaScraper, AmazonScraper, EbayScraper)
```

使用：

```bash
pricemon --site ebay -c cookies.txt -k "servo motor"
```

## 项目结构

```
pricemon/
├── pyproject.toml          # 包配置
├── .github/workflows/ci.yml  # CI 跨平台测试 + 自动发布
├── LICENSE                 # 非商业免费
├── README.md
├── pricemon.py             # 兼容入口
└── pricemon/               # Python 包
    ├── __init__.py
    ├── __main__.py         # python -m pricemon
    ├── cli.py              # CLI + 主流程
    ├── config.py           # 常量配置
    ├── models.py           # Product, ScrapeResult
    ├── cookies.py          # CookieLoader
    ├── browser.py          # Browser 封装
    ├── store.py            # ResultStore + PriceComparator
    ├── output.py           # 终端输出
    └── scrapers/           # 抓取器（可扩展）
        ├── __init__.py     # 注册表
        ├── base.py         # BaseScraper 抽象基类
        ├── alibaba.py      # Alibaba 实现
        └── amazon.py       # Amazon 实现
```

## 发布新版本

```bash
# 1. 更新版本号
#    pricemon/config.py 中的 VERSION
#    pyproject.toml 中的 version

# 2. 构建
uv build

# 3. 发布到 TestPyPI
uv publish --repository testpypi

# 4. 确认无误后发布到 PyPI
uv publish

# 或者用 git tag 触发 CI 自动发布
git tag v0.3.0
git push origin v0.3.0
```

### CI 自动发布

- 推送到 `main` 分支 → 自动发布到 TestPyPI
- 打 `v*` tag → 自动发布到 PyPI

需要在 GitHub 仓库 Settings → Secrets 中配置：
- `TESTPYPI_API_TOKEN`
- `PYPI_API_TOKEN`

## 示例结果

| 网站 | 文件 | 产品数 |
|------|------|--------|
| Alibaba | [results/examples/alibaba_servo_motor.json](results/examples/alibaba_servo_motor.json) | 5 条示例 |
| Amazon | [results/examples/amazon_servo_motor.json](results/examples/amazon_servo_motor.json) | 5 条示例 |

## 常见问题

### Q: 遇到验证码

Cookie 过期或未提供 Cookie。两种解决方式：
- **推荐**：重新登录目标网站，获取新 `document.cookie`，更新 `cookies.txt`
- **不提供 Cookie**：不使用 `--headless`，手动通过验证码后继续

### Q: 抓取结果为 0

1. Cookie 过期 → 重新获取
2. 页面未完全加载 → 不用 `--headless` 试试
3. 网络问题 → 检查连接

### Q: Cookie 有效期多久

- 未登录：几小时到 1 天
- 已登录：数天到数周
- 建议：每周重新获取

## License

非商业免费使用。商业使用需获得授权。详见 [LICENSE](LICENSE)。
