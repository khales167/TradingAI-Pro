from core.portfolio import PortfolioManager

portfolio = PortfolioManager()

portfolio.add_position(
    "NVDA",
    10,
    207.87
)

print(portfolio.summary())

print()

print(portfolio.load_database_positions())