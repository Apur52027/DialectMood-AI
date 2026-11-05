
import json
import re
from pathlib import Path
from collections import Counter

from langchain_core.messages import SystemMessage, HumanMessage
from llm import get_llm


# =====================================================
# CONFIGURATION
# =====================================================

BASE_DIR = Path(__file__).resolve().parent
VOCAB_DIR = BASE_DIR / "vocabulary"

ALLOWED_DIALECTS = [
    "Dinajpur",
    "Rangpur",
    "Standard Bangla",
    "Other/Uncertain"
]

# If Rangpur and Dinajpur evidence is equal,
# select this dialect.
OVERLAP_FALLBACK_DIALECT = "Rangpur"


# =====================================================
# WORD NORMALIZATION
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
# VOCABULARY LOADING
# =====================================================

def load_vocabulary(filename):

    file_path = VOCAB_DIR / filename

    if not file_path.exists():

        print(f"Warning: {filename} not found!")

        return set()

    content = file_path.read_text(
        encoding="utf-8"
    )

    # Remove comment lines
    content = "\n".join(
        line for line in content.splitlines()
        if not line.strip().startswith("#")
    )

    words = re.split(r"[,،\n]+", content)

    return {
        normalize_word(word)
        for word in words
        if normalize_word(word)
    }


# =====================================================
# LOAD DIALECT VOCABULARIES
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

# Words available in both regional dictionaries
OVERLAP_WORDS = (
    RANGPUR_WORDS & DINAJPUR_WORDS
)

# Truly district-specific words
RANGPUR_EXCLUSIVE = (
    RANGPUR_WORDS - DINAJPUR_WORDS
)

DINAJPUR_EXCLUSIVE = (
    DINAJPUR_WORDS - RANGPUR_WORDS
)


# =====================================================
# VOCABULARY-BASED DETECTION
# =====================================================

def vocabulary_detection(text):

    tokens = tokenize(text)

    token_counts = Counter(tokens)

    # Find matched words
    rangpur_matches = {
        word for word in token_counts
        if word in RANGPUR_WORDS
    }

    dinajpur_matches = {
        word for word in token_counts
        if word in DINAJPUR_WORDS
    }

    shared_matches = {
        word for word in token_counts
        if word in SHARED_WORDS
    }

    overlap_matches = (
        rangpur_matches & dinajpur_matches
    )

    rangpur_exclusive_matches = (
        rangpur_matches - DINAJPUR_WORDS
    )

    dinajpur_exclusive_matches = (
        dinajpur_matches - RANGPUR_WORDS
    )

    # Count occurrences instead of unique words
    rangpur_score = sum(
        token_counts[word]
        for word in rangpur_exclusive_matches
    )

    dinajpur_score = sum(
        token_counts[word]
        for word in dinajpur_exclusive_matches
    )

    overlap_score = sum(
        token_counts[word]
        for word in overlap_matches
    )

    shared_score = sum(
        token_counts[word]
        for word in shared_matches
    )

    # -------------------------------------------------
    # CASE 1: No regional vocabulary evidence
    # -------------------------------------------------

    if not rangpur_matches and not dinajpur_matches:

        return {
            "detected": False,
            "rangpur_score": 0,
            "dinajpur_score": 0,
            "overlap_score": 0,
            "shared_score": shared_score,
            "rangpur_matches": [],
            "dinajpur_matches": [],
            "overlap_matches": [],
            "shared_matches": sorted(shared_matches)
        }

    # -------------------------------------------------
    # CASE 2: District-specific evidence exists
    # -------------------------------------------------

    if rangpur_score > dinajpur_score:

        dialect = "Rangpur"

        winning_score = rangpur_score
        losing_score = dinajpur_score

        matched_words = sorted(
            rangpur_exclusive_matches
        )

    elif dinajpur_score > rangpur_score:

        dialect = "Dinajpur"

        winning_score = dinajpur_score
        losing_score = rangpur_score

        matched_words = sorted(
            dinajpur_exclusive_matches
        )

    # -------------------------------------------------
    # CASE 3: Both dialects overlap or scores tie
    # -------------------------------------------------

    elif overlap_score > 0 or (
        rangpur_score > 0 and dinajpur_score > 0
    ):

        dialect = OVERLAP_FALLBACK_DIALECT

        winning_score = max(
            rangpur_score,
            dinajpur_score
        )

        losing_score = winning_score

        matched_words = sorted(
            overlap_matches
        )

    else:

        return {
            "detected": False,
            "rangpur_score": rangpur_score,
            "dinajpur_score": dinajpur_score,
            "overlap_score": overlap_score,
            "shared_score": shared_score,
            "rangpur_matches": sorted(rangpur_matches),
            "dinajpur_matches": sorted(dinajpur_matches),
            "overlap_matches": sorted(overlap_matches),
            "shared_matches": sorted(shared_matches)
        }

    # -------------------------------------------------
    # CONFIDENCE ESTIMATION
    # -------------------------------------------------

    if winning_score == losing_score:

        confidence = 0.68

    else:

        confidence = min(
            0.95,
            0.72 + (
                (winning_score - losing_score)
                / max(winning_score + losing_score, 1)
            ) * 0.20
        )

    return {

        "detected": True,

        "dialect": dialect,

        "confidence": round(confidence, 2),

        "rangpur_score": rangpur_score,

        "dinajpur_score": dinajpur_score,

        "overlap_score": overlap_score,

        "shared_score": shared_score,

        "rangpur_matches": sorted(rangpur_matches),

        "dinajpur_matches": sorted(dinajpur_matches),

        "overlap_matches": sorted(overlap_matches),

        "shared_matches": sorted(shared_matches),

        "linguistic_clues": matched_words

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

        raise ValueError("Invalid JSON response.")

    return json.loads(
        content[start:end + 1]
    )


# =====================================================
# LLM-BASED DIALECT DETECTION
# =====================================================

def llm_dialect_detection(text, evidence):

    system_prompt = f"""
You are an expert Bangla regional linguist.

Identify the likely dialect of the given text.

Available labels:

1. Dinajpur
2. Rangpur
3. Standard Bangla
4. Other/Uncertain

LINGUISTIC INSTRUCTIONS:

- Analyze regional vocabulary.
- Analyze grammar and sentence structure.
- Consider pronouns and verb conjugations.
- Consider regional expressions.
- Consider spelling variations.
- Consider Bangla-English code mixing.
- Analyze the entire sentence, not just one word.
- Do not assume every North Bengal word is exclusive
  to Rangpur or Dinajpur.
- Dinajpur and Rangpur dialects can overlap.
- If there is reasonable evidence for either regional
  dialect, choose the more likely one.
- If both are equally likely, choose Rangpur.
- Do not automatically classify a short sentence
  as Standard Bangla.
- Do not invent linguistic clues.

VOCABULARY EVIDENCE:

{json.dumps(evidence, ensure_ascii=False)}

IMPORTANT:

Shared vocabulary cannot independently prove
a particular district.

Return ONLY valid JSON:

{{
    "dialect": "Dinajpur",
    "confidence": 0.80,
    "explanation": "বাংলায় ব্যাখ্যা",
    "linguistic_clues": ["আঞ্চলিক শব্দ"],
    "alternative": "Rangpur"
}}

Confidence is an uncalibrated model estimate.
Use Other/Uncertain only when there is insufficient
linguistic evidence.
"""

    response = get_llm().invoke([

        SystemMessage(content=system_prompt),

        HumanMessage(content=text)

    ])

    return extract_json(response.content)


# =====================================================
# MAIN DIALECT IDENTIFICATION FUNCTION
# =====================================================

def identify_dialect(text):

    # ---------------------------------------------
    # STEP 1: Empty input
    # ---------------------------------------------

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
    # STEP 2: Vocabulary detection
    # ---------------------------------------------

    evidence = vocabulary_detection(text)

    # ---------------------------------------------
    # STEP 3: Regional vocabulary result
    # ---------------------------------------------

    if evidence["detected"]:

        dialect = evidence["dialect"]

        overlap = evidence["overlap_matches"]

        if overlap:

            explanation = (
                "Dinajpur এবং Rangpur dialect-এর "
                "কিছু overlapping আঞ্চলিক শব্দ পাওয়া গেছে। "
                f"নির্ধারিত tie-breaking নিয়ম অনুযায়ী "
                f"{dialect} নির্বাচন করা হয়েছে।"
            )

        else:

            explanation = (
                "আঞ্চলিক vocabulary matching-এর মাধ্যমে "
                f"{dialect} dialect শনাক্ত করা হয়েছে।"
            )

        return {

            "dialect": dialect,

            "confidence": evidence["confidence"],

            "explanation": explanation,

            "linguistic_clues": (
                evidence["linguistic_clues"]
            ),

            "alternative": (
                "Dinajpur"
                if dialect == "Rangpur"
                else "Rangpur"
            ),

            "method": "Hybrid-Vocabulary",

            "vocabulary_evidence": evidence

        }

    # ---------------------------------------------
    # STEP 4: LLM fallback
    # ---------------------------------------------

    try:

        result = llm_dialect_detection(
            text,
            evidence
        )

    except Exception as error:

        print("Dialect LLM Error:", error)

        return {

            "dialect": "Other/Uncertain",

            "confidence": 0.0,

            "explanation": (
                "ভাষাগত বৈশিষ্ট্য থেকে নিশ্চিত সিদ্ধান্ত "
                "পাওয়া যায়নি।"
            ),

            "linguistic_clues": [],

            "alternative": None,

            "method": "Fallback",

            "vocabulary_evidence": evidence

        }

    # ---------------------------------------------
    # STEP 5: Validate LLM result
    # ---------------------------------------------

    dialect = result.get("dialect")

    if dialect not in ALLOWED_DIALECTS:

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

    if alternative not in ALLOWED_DIALECTS:

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
