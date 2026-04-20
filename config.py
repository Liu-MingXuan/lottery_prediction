import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "lottery.db")

# 双色球数据源（500.com，福彩官网 WAF 拦截不可用）
SSQ_500_URL = "https://datachart.500.com/ssq/history/newinc/history.php"

# 大乐透数据源（500.com，体彩官网 API 被拦截）
DLT_500_URL = "https://datachart.500.com/dlt/history/newinc/history.php"

# 请求配置
REQUEST_TIMEOUT = 30
REQUEST_DELAY = 1.5
USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)

# 概率分析权重
WEIGHT_BASE_FREQ = 0.3
WEIGHT_RECENT_FREQ = 0.4
WEIGHT_MISS = 0.3
RECENT_PERIODS = 100
