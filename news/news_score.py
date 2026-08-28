from news.news_keywords import (
    POSITIVE_KEYWORDS,
    NEGATIVE_KEYWORDS
)


class NewsScore:

    def calculate(self, headlines):

        score = 0

        positive = []
        negative = []

        if not headlines:
            return {
                "score": 0,
                "positive": [],
                "negative": [],
                "keywords": []
            }

        for headline in headlines:

            text = (
                headline.get("title", "") + " " +
                headline.get("summary", "")
            ).lower()

            # Positive keywords
            for word, value in POSITIVE_KEYWORDS.items():

                if word in text:
                    score += value

                    if word not in positive:
                        positive.append(word)

            # Negative keywords
            for word, value in NEGATIVE_KEYWORDS.items():

                if word in text:
                    score += value

                    if word not in negative:
                        negative.append(word)

        # Limit score
        score = max(-20, min(30, score))

        return {

            "score": score,

            "positive": positive,

            "negative": negative,

            "keywords": positive + negative

        }