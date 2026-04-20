import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "lottery.db")

# 双色球数据源（500.com）
SSQ_500_URL = "https://datachart.500.com/ssq/history/newinc/history.php"

# 大乐透数据源（500.com）
DLT_500_URL = "https://datachart.500.com/dlt/history/newinc/history.php"

# 请求配置
REQUEST_TIMEOUT = 30
USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)

# 概率分析权重
WEIGHT_BASE_FREQ = 0.3
WEIGHT_RECENT_FREQ = 0.4
WEIGHT_MISS = 0.3
RECENT_PERIODS = 100

# 多历史阶段分析
ANALYSIS_PERIODS = [10, 50, 100]

# 预测使用的最近期数（只取最近 N 期作为预测基础）
PREDICTION_SPAN = 10

# 子组合惩罚权重：组合越大惩罚越重
COMBO_PENALTY_WEIGHTS = {2: 1, 3: 2, 4: 3, 5: 4, 6: 5}

# 候选池大小（从概率最高的 N 个号码中用贪心算法选取最终推荐）
CANDIDATE_POOL_SIZE = 20
