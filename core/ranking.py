class RankingEngine:

    def rank(self, results):

        return sorted(
            results,
            key=lambda x: (
                x["Score"],
                x["Confidence"],
                x["RVOL"]
            ),
            reverse=True
        )