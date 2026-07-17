import csv
from pathlib import Path


class ReportGenerator:

    def __init__(self):
        Path("reports").mkdir(exist_ok=True)

    def save_csv(self, results):

        filename = "reports/watchlist.csv"

        with open(filename, "w", newline="", encoding="utf-8") as f:

            writer = csv.writer(f)

            # رأس الجدول
            writer.writerow([
    "Symbol",
    "Price",
    "ADX",
    "RVOL",
    "Score",
    "Confidence",
    "Reasons"
])

            # البيانات
            for stock in results:

                writer.writerow([
    stock["Symbol"],
    stock["Price"],
    stock["ADX"],
    stock["RVOL"],
    stock["Score"],
    stock["Confidence"],
    stock["Reasons"]
])

        print(f"\n✅ Report saved: {filename}")