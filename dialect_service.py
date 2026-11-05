# import json

# from langchain_core.messages import (
#     SystemMessage,
#     HumanMessage
# )

# from llm import get_llm


# def extract_json(content):

#     if isinstance(content, list):

#         content = "".join(
#             item.get("text", "")
#             if isinstance(item, dict)
#             else str(item)
#             for item in content
#         )

#     content = str(content).strip()

#     if content.startswith("```"):

#         content = content.split("\n", 1)[-1]

#         content = content.rsplit("```", 1)[0]

#     start = content.find("{")
#     end = content.rfind("}")

#     if start == -1 or end == -1:

#         raise ValueError("Invalid JSON response.")

#     return json.loads(content[start:end + 1])


# def identify_dialect(text):

#     system_prompt = """
# You are an expert Bangla regional linguist.

# Analyze the given text and identify its likely dialect.

# Available labels:

# 1. Dinajpur
# 2. Rangpur
# 3. Standard Bangla
# 4. Other/Uncertain

# Consider:

# - Regional vocabulary
# - Grammar
# - Sentence structure
# - Regional expressions
# - Dialect-specific word forms
# - Bangla-English mixing

# IMPORTANT:

# Dinajpur and Rangpur dialects may overlap.
# Do not make unsupported claims.
# If the text is too short or ambiguous,
# select Other/Uncertain.

# Regional dialects are valid language varieties,
# not incorrect forms of Bangla.

# Return ONLY JSON:

# {
#     "dialect": "Dinajpur",
#     "confidence": 0.85,
#     "explanation": "বাংলায় ব্যাখ্যা",
#     "linguistic_clues": ["শব্দ ১", "শব্দ ২"],
#     "alternative": "Rangpur"
# }

# Confidence is an uncalibrated model estimate.
# """

#     response = get_llm().invoke([
#         SystemMessage(content=system_prompt),
#         HumanMessage(content=text)
#     ])

#     result = extract_json(response.content)

#     allowed = [
#         "Dinajpur",
#         "Rangpur",
#         "Standard Bangla",
#         "Other/Uncertain"
#     ]

#     if result.get("dialect") not in allowed:

#         result["dialect"] = "Other/Uncertain"

#     result["confidence"] = max(
#         0.0,
#         min(1.0, float(result.get("confidence", 0)))
#     )

#     result["linguistic_clues"] = (
#         result.get("linguistic_clues", [])
#     )

#     return result

import json
import re
from pathlib import Path

from langchain_core.messages import (
    SystemMessage,
    HumanMessage
)

from llm import get_llm


# =====================================================
# VOCABULARY CONFIGURATION
# =====================================================

BASE_DIR = Path(__file__).resolve().parent

VOCAB_DIR = BASE_DIR / "vocabulary"


def load_vocabulary(filename):
    """
    Load vocabulary from TXT file.
    Supports comma-separated and line-separated words.
    """

    file_path = VOCAB_DIR / filename

    if not file_path.exists():
        return set()

    content = file_path.read_text(encoding="utf-8")

    words = re.split(r"[,،\n]+", content)

    return {
        normalize_word(word)
        for word in words
        if normalize_word(word)
        and not word.strip().startswith("#")
    }


# =====================================================
# TEXT NORMALIZATION
# =====================================================

def normalize_word(word):

    word = str(word).strip().lower()

    word = re.sub(
        r"[^\u0980-\u09FF]",
        "",
        word
    )

    return word


def tokenize(text):

    return re.findall(
        r"[\u0980-\u09FF]+",
        str(text).lower()
    )


# =====================================================
# LOAD VOCABULARIES
# =====================================================

SHARED_WORDS = load_vocabulary(
    "north_bengal_shared.txt"
)

RANGPUR_WORDS = load_vocabulary(
    "rangpur.txt"
)

DINAJPUR_WORDS = load_vocabulary(
    "dinajpur.txt"
)


# =====================================================
# VOCABULARY BASED DETECTION
# =====================================================

def vocabulary_detection(text):

    tokens = tokenize(text)

    unique_tokens = set(tokens)

    shared_matches = (
        unique_tokens & SHARED_WORDS
    )

    rangpur_matches = (
        unique_tokens & RANGPUR_WORDS
    )

    dinajpur_matches = (
        unique_tokens & DINAJPUR_WORDS
    )

    rangpur_score = len(rangpur_matches)

    dinajpur_score = len(dinajpur_matches)

    total_specific = (
        rangpur_score + dinajpur_score
    )

    # No district-specific evidence
    if total_specific == 0:

        return {
            "detected": False,
            "shared_matches": sorted(shared_matches),
            "rangpur_matches": [],
            "dinajpur_matches": [],
            "rangpur_score": 0,
            "dinajpur_score": 0
        }

    difference = abs(
        rangpur_score - dinajpur_score
    )

    # Require at least two district-specific
    # vocabulary matches and a clear margin.
    if total_specific < 2 or difference < 2:

        return {
            "detected": False,
            "shared_matches": sorted(shared_matches),
            "rangpur_matches": sorted(rangpur_matches),
            "dinajpur_matches": sorted(dinajpur_matches),
            "rangpur_score": rangpur_score,
            "dinajpur_score": dinajpur_score
        }

    if rangpur_score > dinajpur_score:

        dialect = "Rangpur"

        winning_score = rangpur_score

    else:

        dialect = "Dinajpur"

        winning_score = dinajpur_score

    confidence = min(
        0.95,
        0.70 + (
            difference / total_specific
        ) * 0.20
    )

    return {
        "detected": True,
        "dialect": dialect,
        "confidence": round(confidence, 2),
        "shared_matches": sorted(shared_matches),
        "rangpur_matches": sorted(rangpur_matches),
        "dinajpur_matches": sorted(dinajpur_matches),
        "rangpur_score": rangpur_score,
        "dinajpur_score": dinajpur_score
    }


# =====================================================
# JSON EXTRACTION
# =====================================================

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

        raise ValueError(
            "Invalid JSON response."
        )

    return json.loads(
        content[start:end + 1]
    )


# =====================================================
# LLM BASED DIALECT DETECTION
# =====================================================

def llm_dialect_detection(text, evidence):

    system_prompt = """
You are an expert Bangla regional linguist.

Your task is to identify the likely dialect
of the given Bangla text.

Available labels:

1. Dinajpur
2. Rangpur
3. Standard Bangla
4. Other/Uncertain

IMPORTANT LINGUISTIC RULES:

- Focus on regional vocabulary.
- Analyze grammar and sentence structure.
- Consider verb conjugation and pronouns.
- Consider regional expressions.
- Consider dialect-specific word forms.
- Consider Bangla-English code mixing.
- Consider spelling variations.
- Do not assume that every North Bengal word
  belongs exclusively to Rangpur or Dinajpur.
- Dinajpur and Rangpur dialects can overlap.
- Shared vocabulary is not sufficient evidence
  to distinguish these two districts.
- If the text is too short or ambiguous,
  choose Other/Uncertain.
- Never invent linguistic evidence.

VOCABULARY EVIDENCE:

The following information comes from
a manually collected North Bengal vocabulary:

{evidence}

Use these matches as supporting evidence.
Do not treat shared words as district-specific.

The vocabulary-based classifier did not find
sufficient evidence to make a reliable
district-level decision.

Confidence is an uncalibrated model estimate.

Return ONLY valid JSON:

{{
    "dialect": "Dinajpur",
    "confidence": 0.85,
    "explanation": "বাংলায় ব্যাখ্যা",
    "linguistic_clues": ["শব্দ ১", "শব্দ ২"],
    "alternative": "Rangpur"
}}

If no reasonable alternative exists,
use null for alternative.
"""

    prompt = system_prompt.format(
        evidence=json.dumps(
            evidence,
            ensure_ascii=False
        )
    )

    response = get_llm().invoke([

        SystemMessage(content=prompt),

        HumanMessage(content=text)

    ])

    return extract_json(response.content)


# =====================================================
# MAIN DIALECT IDENTIFICATION FUNCTION
# =====================================================

def identify_dialect(text):

    if not text or not str(text).strip():

        return {
            "dialect": "Other/Uncertain",
            "confidence": 0.0,
            "explanation": "কোনো টেক্সট প্রদান করা হয়নি।",
            "linguistic_clues": [],
            "alternative": None,
            "method": "No Input"
        }

    text = str(text).strip()

    # ---------------------------------------------
    # STEP 1: Vocabulary-based detection
    # ---------------------------------------------

    evidence = vocabulary_detection(text)

    # ---------------------------------------------
    # STEP 2: Strong vocabulary evidence
    # ---------------------------------------------

    if evidence["detected"]:

        dialect = evidence["dialect"]

        matched_words = (
            evidence["rangpur_matches"]
            if dialect == "Rangpur"
            else evidence["dinajpur_matches"]
        )

        return {

            "dialect": dialect,

            "confidence": evidence["confidence"],

            "explanation": (
                "যাচাইকৃত আঞ্চলিক শব্দভান্ডারের "
                "সাথে মিল পাওয়া গেছে। "
                "এই শব্দগুলোর ভিত্তিতে "
                f"{dialect} dialect শনাক্ত করা হয়েছে।"
            ),

            "linguistic_clues": matched_words,

            "alternative": (
                "Dinajpur"
                if dialect == "Rangpur"
                else "Rangpur"
            ),

            "method": "Vocabulary-Based",

            "vocabulary_evidence": evidence

        }

    # ---------------------------------------------
    # STEP 3: LLM fallback
    # ---------------------------------------------

    result = llm_dialect_detection(
        text,
        evidence
    )

    allowed = [
        "Dinajpur",
        "Rangpur",
        "Standard Bangla",
        "Other/Uncertain"
    ]

    dialect = result.get("dialect")

    if dialect not in allowed:

        dialect = "Other/Uncertain"

    try:

        confidence = float(
            result.get("confidence", 0)
        )

    except (ValueError, TypeError):

        confidence = 0.0

    confidence = max(
        0.0,
        min(1.0, confidence)
    )

    clues = result.get(
        "linguistic_clues", []
    )

    if not isinstance(clues, list):

        clues = []

    alternative = result.get("alternative")

    if alternative not in allowed:

        alternative = None

    return {

        "dialect": dialect,

        "confidence": round(confidence, 2),

        "explanation": result.get(
            "explanation",
            "ভাষাগত বৈশিষ্ট্য বিশ্লেষণ করা হয়েছে।"
        ),

        "linguistic_clues": clues,

        "alternative": alternative,

        "method": "LLM-Based",

        "vocabulary_evidence": evidence

    }

