from strategy.score_engine import ScoreEngine

engine = ScoreEngine()

engine.add_news(True)

engine.add_ma(
    ma19=210,
    ma38=205,
    ma209=180
)

engine.add_dmi(
    di_plus=35,
    di_minus=12,
    adx=31
)

engine.add_volume(3.5)

engine.add_pvp(True)

score, reasons = engine.result()

print("=" * 50)
print("TRADING AI SCORE")
print("=" * 50)

print(f"Score : {score}/100\n")

for reason in reasons:
    print(reason)