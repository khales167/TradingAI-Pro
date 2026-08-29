import sqlite3
from pathlib import Path
from config import MAX_OPEN_POSITIONS


class DatabaseManager:
    def position_exists(self, symbol):

        conn = self.connect()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT COUNT(*)
            FROM portfolio
            WHERE symbol = ?
            AND status = 'OPEN'
        """, (symbol,))

        exists = cursor.fetchone()[0] > 0

        conn.close()

        return exists
    def __init__(self):
        Path("database").mkdir(exist_ok=True)
        self.db_path = "database/trading_ai.db"
        self.create_tables()

    def connect(self):

        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row

        return conn

    def create_tables(self):

        conn = self.connect()
        cursor = conn.cursor()

        # ========================
        # SCANS TAB3.6201LE
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
           stop_price REAL,
           target_price REAL,

           entry_date TEXT,

           status TEXT
     )
        """)
            # ===========================
        # PORTFOLIO MIGRATION
        # ===========================

        cursor.execute("PRAGMA table_info(portfolio)")
        columns = [
            row[1]
            for row in cursor.fetchall()
        ]

        if "exit_price" not in columns:
            cursor.execute(
                "ALTER TABLE portfolio ADD COLUMN exit_price REAL"
            )

        if "exit_date" not in columns:
            cursor.execute(
                "ALTER TABLE portfolio ADD COLUMN exit_date TEXT"
            )

        if "realized_pl" not in columns:
            cursor.execute(
                "ALTER TABLE portfolio ADD COLUMN realized_pl REAL"
            )

        if "realized_pl_percent" not in columns:
            cursor.execute(
                """
                ALTER TABLE portfolio
                ADD COLUMN realized_pl_percent REAL
                """
            )    
        if "break_even_activated" not in columns:
            cursor.execute("""
                ALTER TABLE portfolio
                ADD COLUMN break_even_activated INTEGER DEFAULT 0
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
        stop_price,
        target_price,
        entry_date
    ):

        conn = self.connect()
        cursor = conn.cursor()

        cursor.execute("""

        INSERT INTO portfolio(

            symbol,
            quantity,
            entry_price,
            stop_price,
            target_price,
            entry_date,
            status

        )

        VALUES(?,?,?,?,?,?,?)

        """, (

            symbol,
            quantity,
            entry_price,
            stop_price,
            target_price,
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
            stop_price,
            target_price,
            entry_date,
            status,
            break_even_activated

        FROM portfolio

        WHERE status='OPEN'

""")

        rows = cursor.fetchall()

        conn.close()

        return rows
    def add_demo_position(self):

        conn = self.connect()
        cursor = conn.cursor()

        cursor.execute("""
        INSERT INTO portfolio(

          symbol,
          quantity,
          entry_price,
          stop_price,
          target_price,
          entry_date,
          status

     )

        VALUES(?,?,?,?,?,?,?)

    """, (

             "NVDA",
             10,
             190.00,
             180.00,
             220.00,
             "2026-07-30 12:00:00",
             "OPEN"

    ))

        conn.commit()
        conn.close()
    def clear_portfolio(self):

        conn = self.connect()
        cursor = conn.cursor()

        cursor.execute("DELETE FROM portfolio")

        conn.commit()
        conn.close()

        print("✅ Portfolio cleared.")    

    def close_position(
        self,
        symbol,
        exit_price,
        exit_date
    ):

        conn = self.connect()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                quantity,
                entry_price

            FROM portfolio

            WHERE symbol = ?
            AND status = 'OPEN'
        """, (symbol,))

        position = cursor.fetchone()

        if position is None:

            conn.close()

            print(
                f"⚠ No open position found for {symbol}."
            )

            return False

        quantity = position["quantity"]
        entry_price = position["entry_price"]

        realized_pl = (
            exit_price - entry_price
        ) * quantity

        realized_pl_percent = (
            (exit_price - entry_price)
            / entry_price
        ) * 100

        cursor.execute("""
            UPDATE portfolio

            SET
                status = 'CLOSED',
                exit_price = ?,
                exit_date = ?,
                realized_pl = ?,
                realized_pl_percent = ?

            WHERE symbol = ?
            AND status = 'OPEN'
        """, (
            exit_price,
            exit_date,
            round(realized_pl, 2),
            round(realized_pl_percent, 2),
            symbol
        ))

        conn.commit()
        conn.close()

        print(
            f"✅ {symbol} position closed "
            f"at ${exit_price:.2f}"
        )

        print(
            f"Realized P/L: "
            f"${realized_pl:.2f} "
            f"({realized_pl_percent:.2f}%)"
        )

        return True
    def activate_break_even(self, symbol, entry_price):

        conn = self.connect()
        cursor = conn.cursor()

        cursor.execute("""
             UPDATE portfolio

             SET
                    stop_price = ?,
                    break_even_activated = 1

             WHERE symbol = ?
             AND status = 'OPEN'
        """, (
             entry_price,
             symbol
    ))

        conn.commit()
        conn.close()

        print(
            f"✅ {symbol} BREAK-EVEN activated. "
            f"Stop moved to ${entry_price:.2f}"
    )
    def update_stop(self, symbol, new_stop):

        conn = self.connect()
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE portfolio
            SET stop_price = ?
            WHERE symbol = ?
            AND status = 'OPEN'
        """, (
            round(new_stop, 2),
            symbol
        ))

        conn.commit()
        conn.close()

        print(
            f"✅ {symbol} Trailing Stop updated "
            f"to ${new_stop:.2f}"
        )

        return True
    def get_closed_positions(self):

        conn = self.connect()
        cursor = conn.cursor()

        cursor.execute("""
           SELECT
              symbol,
              quantity,
              entry_price,
              stop_price,
              target_price,
              entry_date,
              exit_price,
              exit_date,
              realized_pl,
              realized_pl_percent,
              status

            FROM portfolio

            WHERE status = 'CLOSED'

            ORDER BY exit_date DESC
        """)
  
        rows = cursor.fetchall()

        conn.close()

        return rows


    def get_performance_summary(self):

        positions = self.get_closed_positions()

        total_trades = len(positions)

        if total_trades == 0:

            return {
                "total_trades": 0,
                "winners": 0,
                "losers": 0,
                "win_rate": 0,
                "total_realized_pl": 0,
                "average_pl": 0,
                "average_win": 0,
                "average_loss": 0,
                "profit_factor": 0,
                "best_trade": 0,
                "worst_trade": 0,
                "expectancy": 0
            }

        wins = []
        losses = []
        all_pl = []

        for position in positions:

            pl = position["realized_pl"] or 0

            all_pl.append(pl)

            if pl > 0:
                wins.append(pl)

            elif pl < 0:
                losses.append(pl)

        winners = len(wins)
        losers = len(losses)

        total_realized_pl = sum(all_pl)

        win_rate = (
            winners / total_trades
        ) * 100

        average_pl = (
            total_realized_pl / total_trades
        )

        # ==========================================
        # AVERAGE WIN / LOSS
        # ==========================================

        average_win = (
            sum(wins) / len(wins)
            if wins else 0
        )

        average_loss = (
            sum(losses) / len(losses)
            if losses else 0
        )

        # ==========================================
        # PROFIT FACTOR
        # ==========================================

        gross_profit = sum(wins)

        gross_loss = abs(sum(losses))

        if gross_loss > 0:
            profit_factor = gross_profit / gross_loss
        elif gross_profit > 0:
            profit_factor = float("inf")
        else:
            profit_factor = 0

        # ==========================================
        # BEST / WORST TRADE
        # ==========================================

        best_trade = max(all_pl)
        worst_trade = min(all_pl)

        # ==========================================
        # EXPECTANCY
        # ==========================================

        win_probability = winners / total_trades
        loss_probability = losers / total_trades

        expectancy = (
            win_probability * average_win
            +
            loss_probability * average_loss
        )

        return {
            "total_trades": total_trades,
            "winners": winners,
            "losers": losers,
            "win_rate": round(win_rate, 2),
            "total_realized_pl": round(total_realized_pl, 2),
            "average_pl": round(average_pl, 2),
            "average_win": round(average_win, 2),
            "average_loss": round(average_loss, 2),
            "profit_factor": (
                round(profit_factor, 2)
                if profit_factor != float("inf")
                else float("inf")
            ),
            "best_trade": round(best_trade, 2),
            "worst_trade": round(worst_trade, 2),
            "expectancy": round(expectancy, 2)
        }
    def get_open_positions_count(self):

        conn = self.connect()
        cursor = conn.cursor()

        cursor.execute("""
              SELECT COUNT(*)
              FROM portfolio
              WHERE status = 'OPEN'
            """)

        count = cursor.fetchone()[0]

        conn.close()

        return count