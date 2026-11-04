from langchain_core.messages import (
    SystemMessage,
    HumanMessage
)

from dialect_service import extract_json
from llm import get_llm


def analyze_sentiment(text):

    system_prompt = """
You are a Bangla sentiment analysis expert.

Analyze the emotional meaning of the text.

Consider:
- Standard Bangla
- Dinajpur dialect
- Rangpur dialect
- Informal language
- Sarcasm
- Emotional vocabulary
- Context

Available sentiment labels:

Positive
Negative
Neutral
Mixed

Return ONLY JSON:

{
    "sentiment": "Positive",
    "confidence": 0.90,
    "positive_score": 80,
    "negative_score": 5,
    "neutral_score": 15,
    "explanation": "বাংলায় ব্যাখ্যা",
    "emotional_words": ["ভালো", "সুন্দর"],
    "suggestion": "একটি ছোট পরামর্শ"
}

The three scores must sum to 100.

Confidence is a model estimate, not a calibrated probability.

Do not diagnose mental health from a text.
"""

    response = get_llm().invoke([
        SystemMessage(content=system_prompt),
        HumanMessage(content=text)
    ])

    result = extract_json(response.content)

    allowed = [
        "Positive",
        "Negative",
        "Neutral",
        "Mixed"
    ]

    if result.get("sentiment") not in allowed:

        result["sentiment"] = "Neutral"

    scores = []

    for key in [
        "positive_score",
        "negative_score",
        "neutral_score"
    ]:

        try:
            value = float(result.get(key, 0))
        except (ValueError, TypeError):
            value = 0

        scores.append(max(0, value))

    total = sum(scores)

    if total <= 0:

        scores = [0, 0, 100]

    else:

        scores = [
            round(score * 100 / total, 2)
            for score in scores
        ]

        scores[2] = round(
            100 - scores[0] - scores[1],
            2
        )

    result["positive_score"] = scores[0]
    result["negative_score"] = scores[1]
    result["neutral_score"] = scores[2]

    result["confidence"] = max(
        0.0,
        min(1.0, float(result.get("confidence", 0)))
    )

    return result