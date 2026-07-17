from core.database import DatabaseManager

db = DatabaseManager()

print("Database created successfully.")

rows = db.get_all_scans()

print(rows)