import sqlite3
from pathlib import Path


class DatabaseManager:

    def __init__(self):
        Path("database").mkdir(exist_ok=True)
        self.db_path = "database/trading_ai.db"
        self.create_tables()

    def connect(self):
        return sqlite3.connect(self.db_path)

    def create_tables(self):

        conn = self.connect()
        cursor = conn.cursor()

        # ===========================
        # SCANS TABLE
        # ===========================

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS scans (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            scan_date TEXT,
            scan_time TEXT,

            symbol TEXT,

            price REAL,

            adx REAL,
            atr REAL,
            rvol REAL,

            entry REAL,
            stop REAL,
            target REAL,
            rr REAL,

            score INTEGER,
            confidence INTEGER,

            decision TEXT,
            market TEXT
        )
        """)

        # ===========================
        # PORTFOLIO TABLE
        # ===========================

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS portfolio (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            symbol TEXT,
            quantity INTEGER,

            entry_price REAL,

            entry_date TEXT,

            status TEXT
        )
        """)

        conn.commit()
        conn.close()

    # =====================================
    # SAVE SCAN
    # =====================================

    def save_scan(self, stock, scan_date, scan_time):

        conn = self.connect()
        cursor = conn.cursor()

        cursor.execute("""
        INSERT INTO scans (

            scan_date,
            scan_time,

            symbol,

            price,

            adx,
            atr,
            rvol,

            entry,
            stop,
            target,
            rr,

            score,
            confidence,

            decision,
            market

        )

        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)

        """, (

            scan_date,
            scan_time,

            stock["Symbol"],

            stock["Price"],

            stock["ADX"],
            stock["ATR"],
            stock["RVOL"],

            stock["Entry"],
            stock["Stop"],
            stock["Target"],
            stock["RR"],

            stock["Score"],
            stock["Confidence"],

            stock["Decision"],
            stock["Market"]

        ))

        conn.commit()
        conn.close()

    # =====================================
    # HISTORY
    # =====================================

    def get_all_scans(self):

        conn = self.connect()
        cursor = conn.cursor()

        cursor.execute("""
        SELECT *
        FROM scans
        ORDER BY id DESC
        """)

        rows = cursor.fetchall()

        conn.close()

        return rows

    def get_last_scans(self, limit=20):

        conn = self.connect()
        cursor = conn.cursor()

        cursor.execute("""
        SELECT

            scan_date,
            scan_time,

            symbol,

            price,

            score,
            confidence,

            decision,
            market

        FROM scans

        ORDER BY id DESC

        LIMIT ?

        """, (limit,))

        rows = cursor.fetchall()

        conn.close()

        return rows

    # =====================================
    # PORTFOLIO
    # =====================================

    def add_position(
        self,
        symbol,
        quantity,
        entry_price,
        entry_date
    ):

        conn = self.connect()
        cursor = conn.cursor()

        cursor.execute("""

        INSERT INTO portfolio(

            symbol,
            quantity,
            entry_price,
            entry_date,
            status

        )

        VALUES(?,?,?,?,?)

        """, (

            symbol,
            quantity,
            entry_price,
            entry_date,
            "OPEN"

        ))

        conn.commit()
        conn.close()

    def get_portfolio(self):

        conn = self.connect()
        cursor = conn.cursor()

        cursor.execute("""

        SELECT

            symbol,
            quantity,
            entry_price,
            entry_date,
            status

        FROM portfolio

        WHERE status='OPEN'

        """)

        rows = cursor.fetchall()

        conn.close()

        return rows