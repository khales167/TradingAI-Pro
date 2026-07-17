from core.portfolio import PortfolioManager

portfolio = PortfolioManager()

portfolio.add_position("NVDA", 10, 207.87)
portfolio.add_position("AMD", 5, 508.29)

portfolio.display()