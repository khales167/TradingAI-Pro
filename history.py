from core.database import DatabaseManager

db = DatabaseManager()

rows = db.get_last_scans()

print("=" * 90)
print(
    f"{'DATE':<12}"
    f"{'TIME':<10}"
    f"{'SYMBOL':<10}"
    f"{'PRICE':>10}"
    f"{'SCORE':>8}"
    f"{'CONF':>8}"
    f"{'ACTION':>12}"
)

print("-" * 90)

for row in rows:

    print(
        f"{row[0]:<12}"
        f"{row[1]:<10}"
        f"{row[2]:<10}"
        f"{row[3]:>10.2f}"
        f"{row[4]:>8}"
        f"{row[5]:>7}%"
        f"{row[6]:>12}"
    )