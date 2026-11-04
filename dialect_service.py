import json

from langchain_core.messages import (
    SystemMessage,
    HumanMessage
)

from llm import get_llm


def extract_json(content):

    if isinstance(content, list):

        content = "".join(
            item.get("text", "")
            if isinstance(item, dict)
            else str(item)
            for item in content
        )

    content = str(content).strip()

    if content.startswith("```"):

        content = content.split("\n", 1)[-1]

        content = content.rsplit("```", 1)[0]

    start = content.find("{")
    end = content.rfind("}")

    if start == -1 or end == -1:

        raise ValueError("Invalid JSON response.")

    return json.loads(content[start:end + 1])


def identify_dialect(text):

    system_prompt = """
You are an expert Bangla regional linguist.

Analyze the given text and identify its likely dialect.

Available labels:

1. Dinajpur
2. Rangpur
3. Standard Bangla
4. Other/Uncertain

Consider:

- Regional vocabulary
- Grammar
- Sentence structure
- Regional expressions
- Dialect-specific word forms
- Bangla-English mixing

IMPORTANT:

Dinajpur and Rangpur dialects may overlap.
Do not make unsupported claims.
If the text is too short or ambiguous,
select Other/Uncertain.

Regional dialects are valid language varieties,
not incorrect forms of Bangla.

Return ONLY JSON:

{
    "dialect": "Dinajpur",
    "confidence": 0.85,
    "explanation": "বাংলায় ব্যাখ্যা",
    "linguistic_clues": ["শব্দ ১", "শব্দ ২"],
    "alternative": "Rangpur"
}

Confidence is an uncalibrated model estimate.
"""

    response = get_llm().invoke([
        SystemMessage(content=system_prompt),
        HumanMessage(content=text)
    ])

    result = extract_json(response.content)

    allowed = [
        "Dinajpur",
        "Rangpur",
        "Standard Bangla",
        "Other/Uncertain"
    ]

    if result.get("dialect") not in allowed:

        result["dialect"] = "Other/Uncertain"

    result["confidence"] = max(
        0.0,
        min(1.0, float(result.get("confidence", 0)))
    )

    result["linguistic_clues"] = (
        result.get("linguistic_clues", [])
    )

    return result