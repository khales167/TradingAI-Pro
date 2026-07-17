POSITIVE_WORDS = [
    "upgrade",
    "buy",
    "beats",
    "growth",
    "ai",
    "contract",
    "record",
    "strong",
    "surge",
    "partnership"
]


class NewsScore:

    def calculate(self, headlines):

        score = 0
        reasons = []

        for headline in headlines:

            text = headline.lower()

            for word in POSITIVE_WORDS:

                if word in text:
                    score += 5
                    reasons.append(word)

        score = min(score, 15)

        return {
            "score": score,
            "keywords": list(set(reasons))
        }