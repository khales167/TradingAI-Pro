# ==========================
# WATCHLIST (مؤقتًا)
# ==========================

WATCHLIST = [
    "NVDA",
    "AMD",
    "AAPL",
    "TSLA",
    "PLTR",
    "META",
    "MSFT",
    "AMZN",
    "NFLX",
    "AVGO"
]

# ==========================
# STRATEGY
# ==========================

MA_FAST = 19
MA_MID = 38
MA_SLOW = 209

ADX_PERIOD = 14
ADX_LIMIT = 25

RVOL_LIMIT = 2.0

# ==========================
# SCORING
# ==========================

TREND_SCORE = 30
DMI_SCORE = 20
ADX_SCORE = 20
RVOL_SCORE = 15
NEWS_SCORE = 15

MAX_SCORE = (
    TREND_SCORE +
    DMI_SCORE +
    ADX_SCORE +
    RVOL_SCORE +
    NEWS_SCORE
)

# ==========================
# SCANNER
# ==========================

MIN_PRICE = 5
MAX_PRICE = 1000

MIN_VOLUME = 1_000_000

TOP_RESULTS = 10