"""pricemon 全局配置"""

VERSION = "0.0.1"

# 目录
RESULTS_DIR = "results"

# 默认值
DEFAULT_KEYWORD = "DM motor servo"
DEFAULT_TIMEOUT = 15
DEFAULT_SITE = "alibaba"

# 浏览器行为
SCROLL_ROUNDS = 3
SCROLL_PAUSE = 1.5
PAGE_LOAD_WAIT = 5
RETRY_WAIT = 5
DETAIL_WAIT = 2

# 输出
SUMMARY_LIMIT = 10

# 验证码检测信号（通用）
CAPTCHA_SIGNALS = ("baxia-punish", "captcha-intercept", "nocaptcha")
