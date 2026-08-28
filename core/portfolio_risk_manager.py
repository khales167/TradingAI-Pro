from config import MAX_OPEN_POSITIONS


class PortfolioRiskManager:

    def __init__(self, database):
        self.db = database

    def can_open_new_position(self):

        open_positions = (
            self.db.get_open_positions_count()
        )

        available_slots = (
            MAX_OPEN_POSITIONS - open_positions
        )

        if open_positions >= MAX_OPEN_POSITIONS:

            return {
                "allowed": False,
                "open_positions": open_positions,
                "max_positions": MAX_OPEN_POSITIONS,
                "available_slots": 0,
                "reason": (
                    f"MAX OPEN POSITIONS "
                    f"({open_positions}/{MAX_OPEN_POSITIONS})"
                )
            }

        return {
            "allowed": True,
            "open_positions": open_positions,
            "max_positions": MAX_OPEN_POSITIONS,
            "available_slots": available_slots,
            "reason": (
                f"POSITION AVAILABLE "
                f"({open_positions}/{MAX_OPEN_POSITIONS})"
            )
        }