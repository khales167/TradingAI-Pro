from earnings.earnings_calendar import EarningsCalendar

engine = EarningsCalendar()

earnings = engine.get_today()

print("Total Earnings:", len(earnings))

for item in earnings[:10]:

    print(
        item.get("symbol"),
        item.get("date"),
        item.get("hour")
    )
