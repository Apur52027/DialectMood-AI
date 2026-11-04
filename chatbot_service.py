
import re
from functools import lru_cache

from langchain_core.messages import (
    SystemMessage,
    HumanMessage,
    AIMessage
)

from llm import get_llm


# ============================================================
# CONFIGURATION
# ============================================================

RECENT_WINDOW = 20
SUMMARY_STEP = 10

# Negative sentiment score threshold
NEGATIVE_THRESHOLD = 0.40

LOW_MOOD_KEYWORDS = [
    "মন খারাপ", "মন ভালো নেই", "মন ভাল নেই",
    "মন ভাল নাই", "মন ভালো নাই",
    "ভালো লাগে না", "ভাল লাগে না", "ভাল নাগে না",
    "ভালো লাগছে না", "কিছু ভালো লাগে না",
    "হতাশ", "একা লাগ", "একাকী", "কষ্ট",
    "কান্না", "কাঁদ", "ক্লান্ত", "অসহায়",
    "মূল্যহীন", "ডিপ্রেশন", "বিষণ্ণ",
    "দুশ্চিন্তা", "চাপ", "হতাশাগ্রস্ত",
    "depressed", "depression", "hopeless",
    "lonely", "worthless", "exhausted",
    "anxious", "sad", "heartbroken",
    "mon kharap", "mon valo nei",
    "valo lagche na", "valo lage na",
    "bhalo lage na", "eka lage"
]

CRISIS_KEYWORDS = [
    "আত্মহত্যা", "আত্মহানি",
    "মরে যেতে চাই", "মরে যেতে ইচ্ছা",
    "মরতে চাই", "মরে যাই",
    "বাঁচতে চাই না", "বাঁচতে ইচ্ছা করে না",
    "বেঁচে থাকতে চাই না",
    "নিজেকে শেষ করে", "শেষ করে দিতে চাই",
    "হাত কাটতে চাই", "নিজেকে আঘাত",
    "সুইসাইড", "সুইসাইডাল",
    "suicide", "suicidal",
    "kill myself", "want to die",
    "end my life", "self harm",
    "self-harm", "marte chai",
    "morte chai", "bachte chai na"
]

POSITIVE_KEYWORDS = [
    "খুব ভালো", "অনেক ভালো", "মন ভালো",
    "খুশি", "আনন্দ", "সুন্দর দিন",
    "ভালো লাগছে", "ভালো আছি",
    "সফল হয়েছি", "সফল হয়েছি",
    "খুশি হয়েছি", "ভালো খবর",
    "happy", "excited", "feeling good",
    "feeling great", "awesome", "wonderful",
    "i am happy", "i feel good"
]


# ============================================================
# TEXT HELPERS
# ============================================================

def normalize_text(text):
    return re.sub(r"\s+", " ", str(text).lower()).strip()


def contains_keyword(text, keywords):
    text = normalize_text(text)
    return any(keyword in text for keyword in keywords)


def get_sentiment_from_context(mood_context):
    """
    Read sentiment information from Dialect Lab output.

    Expected examples:
    Sentiment: Negative
    sentiment_score: 0.25
    sentiment: positive
    """

    if not mood_context:
        return None

    context = normalize_text(mood_context)

    # Find explicit sentiment label
    match = re.search(
        r"(?:sentiment|emotion)\s*[:=]\s*(positive|negative|neutral)",
        context
    )

    if match:
        return match.group(1)

    # Find sentiment score if available
    match = re.search(
        r"sentiment_score\s*[:=]\s*(-?\d+(?:\.\d+)?)",
        context
    )

    if match:
        score = float(match.group(1))

        # This assumes a 0-to-1 negative sentiment score.
        if score <= NEGATIVE_THRESHOLD:
            return "negative"

        return "positive"

    return None


# ============================================================
# MOOD DETECTION
# ============================================================

def detect_mood_level(
    message,
    recent_user_messages=None,
    mood_context=""
):
    """
    Returns:
        crisis
        persistent_low
        depression_related
        low
        negative
        positive
        normal
    """

    text = normalize_text(message)

    recent = recent_user_messages or []

    # 1. Crisis detection has highest priority
    if contains_keyword(text, CRISIS_KEYWORDS):
        return "crisis"

    # 2. Detect current text mood
    is_low = contains_keyword(text, LOW_MOOD_KEYWORDS)
    is_positive = contains_keyword(text, POSITIVE_KEYWORDS)

    # 3. Read Dialect Lab sentiment
    sentiment = get_sentiment_from_context(mood_context)

    # 4. Detect depression-related expressions
    depression_words = [
        "ডিপ্রেশন", "বিষণ্ণতা", "হতাশাগ্রস্ত",
        "depression", "depressed", "hopeless"
    ]

    depression_related = contains_keyword(
        text, depression_words
    )

    # 5. Count recent negative messages
    recent_low_count = sum(
        1 for msg in recent[-6:]
        if contains_keyword(msg, LOW_MOOD_KEYWORDS)
    )

    # 6. Persistent negative mood
    if is_low and recent_low_count >= 2:
        return "persistent_low"

    if depression_related:
        return "depression_related"

    # 7. Negative sentiment from text or Dialect Lab
    if is_low or sentiment == "negative":
        return "low" if is_low else "negative"

    # 8. Positive mood
    if is_positive or sentiment == "positive":
        return "positive"

    # 9. Normal conversation
    return "normal"


# ============================================================
# SYSTEM PROMPT
# ============================================================

SYSTEM_PROMPT = """
তুমি DialectMood AI-এর একজন সহানুভূতিশীল Bangla Mood Companion।

তুমি বন্ধুর মতো স্বাভাবিকভাবে কথা বলবে।
তোমার প্রধান কাজ হলো ব্যবহারকারীর অনুভূতি বোঝা,
তার কথা মন দিয়ে শোনা এবং কথোপকথন চালিয়ে যাওয়া।

LANGUAGE:
- Standard Bangla-তে উত্তর দেবে।
- ব্যবহারকারী English বা Banglish লিখলে তার ভাষার ধরন অনুসরণ করবে।
- Dinajpur ও Rangpur dialect বুঝবে।
- আঞ্চলিক ভাষা নিয়ে মজা করবে না।

IMPORTANT CONVERSATION RULES:

1. ব্যবহারকারীর অনুভূতি আগে বোঝার চেষ্টা করবে।
2. Negative sentiment দেখলেই depression বলবে না।
3. ব্যবহারকারী কেন এমন অনুভব করছে তা জানার চেষ্টা করবে।
4. আগের কথোপকথন থেকে তথ্য পাওয়া গেলে সেটি ব্যবহার করবে।
5. আগে জানা বিষয় আবার জিজ্ঞাসা করবে না।
6. একই প্রশ্ন বারবার করবে না।
7. ব্যবহারকারী বিস্তারিত বললে তার কথার নির্দিষ্ট অংশ ধরে উত্তর দেবে।
8. একবারে একটি গুরুত্বপূর্ণ প্রশ্ন করবে।
9. ব্যবহারকারী সমাধান চাইলে ছোট ও বাস্তবসম্মত পরামর্শ দেবে।
10. ব্যবহারকারী শুধু কথা বলতে চাইলে তাকে মন দিয়ে শুনবে।

MOOD-BASED RESPONSE:

POSITIVE:
- আনন্দের সঙ্গে উত্তর দেবে।
- তার ভালো লাগার কারণ জানতে চাইতে পারো।
- তার সাফল্য আন্তরিকভাবে উদযাপন করবে।

NEGATIVE:
- প্রথমে তার অনুভূতিকে স্বীকার করবে।
- কেন এমন অনুভব হচ্ছে তা জানার চেষ্টা করবে।
- উদাহরণ: "শুনে খারাপ লাগছে। আজ কি কোনো বিশেষ ঘটনা
  ঘটেছে, নাকি বেশ কিছুদিন ধরেই এমন লাগছে?"
- কারণ না জেনে সমাধান দেওয়ার চেষ্টা করবে না।

DEPRESSION-RELATED:
- ব্যবহারকারীর হতাশা বা দীর্ঘদিনের কষ্টকে গুরুত্ব দেবে।
- রোগ নির্ণয় করবে না।
- কষ্ট কতদিন ধরে হচ্ছে এবং দৈনন্দিন জীবনে
  কী প্রভাব ফেলছে তা ধীরে ধীরে জানতে চাইবে।
- প্রয়োজন হলে বিশ্বস্ত মানুষ বা মানসিক স্বাস্থ্য
  বিশেষজ্ঞের সাহায্য নিতে উৎসাহিত করবে।

PERSISTENT LOW MOOD:
- আগের কথার সঙ্গে বর্তমান অনুভূতি মিলিয়ে উত্তর দেবে।
- কষ্ট বারবার ফিরে আসার বিষয়টি স্বীকার করবে।
- সহানুভূতির সঙ্গে একটি প্রশ্ন করবে।

NORMAL:
- স্বাভাবিক বন্ধুত্বপূর্ণ কথোপকথন চালিয়ে যাবে।
- অকারণে mood বা depression নিয়ে প্রশ্ন করবে না।

GENERAL STYLE:
- সাধারণত ৩-৫টি ছোট বাক্য।
- একসঙ্গে অনেক পরামর্শ দেবে না।
- সর্বোচ্চ একটি emoji।
- "সব ঠিক হয়ে যাবে" বা "চিন্তা করো না" বলবে না।
- বিচার করবে না।

SAFETY:
- তুমি ডাক্তার বা therapist নও।
- কখনো রোগ নির্ণয় করবে না।
- আত্মহানি বা আত্মহত্যার ইঙ্গিত পেলে
  নিরাপত্তাকে সর্বোচ্চ গুরুত্ব দেবে।
- প্রয়োজন হলে সরাসরি জিজ্ঞাসা করবে ব্যবহারকারী
  এই মুহূর্তে নিজেকে আঘাত করার কথা ভাবছে কি না।
- কাছের বিশ্বস্ত মানুষকে জানাতে বলবে।
- তাৎক্ষণিক বিপদে বাংলাদেশের জরুরি নম্বর ৯৯৯
  অথবা নিকটস্থ হাসপাতালের সাহায্য নিতে বলবে।
"""


# ============================================================
# MOOD DIRECTIVES
# ============================================================

MOOD_DIRECTIVES = {

    "positive": """
ব্যবহারকারীর মেজাজ ইতিবাচক।
আন্তরিকভাবে তার আনন্দে অংশ নাও।
কথোপকথন স্বাভাবিকভাবে এগিয়ে নাও।
""",

    "negative": """
ব্যবহারকারীর Dialect Lab অথবা sentiment analysis
থেকে negative sentiment পাওয়া গেছে।

কিন্তু negative sentiment মানেই depression নয়।

প্রথমে তার অনুভূতিকে স্বীকার করো।
তারপর কেন এমন অনুভব হচ্ছে তা জানার চেষ্টা করো।

যদি কারণ জানা না থাকে, একটি নরম প্রশ্ন করো।
এখনই সমাধান বা উপদেশের তালিকা দেবে না।
""",

    "low": """
ব্যবহারকারী নিজের কথায় মন খারাপ বা কষ্ট প্রকাশ করেছে।

তার অনুভূতিকে গুরুত্ব দাও।
কেন এমন লাগছে তা জানতে চাও।
আগের কথার সূত্র থাকলে ব্যবহার করো।
একটি খোলা প্রশ্ন করো।
""",

    "depression_related": """
ব্যবহারকারীর কথায় হতাশা বা depression-related
অনুভূতির ইঙ্গিত রয়েছে।

এটি কোনো clinical diagnosis নয়।

তার কষ্ট মন দিয়ে শোনো।
কতদিন ধরে এমন হচ্ছে এবং কী কারণে হচ্ছে
তা কোমলভাবে জানার চেষ্টা করো।
প্রয়োজনে বিশ্বস্ত মানুষের সহায়তা নিতে উৎসাহ দাও।
""",

    "persistent_low": """
ব্যবহারকারী বারবার মন খারাপের কথা বলছে।

আগের কথোপকথনের সঙ্গে বর্তমান অনুভূতির
সম্পর্ক খুঁজে উত্তর দাও।

কষ্টটি দীর্ঘস্থায়ী হলে বিশ্বস্ত মানুষ বা
মানসিক স্বাস্থ্য বিশেষজ্ঞের সঙ্গে কথা বলার
সম্ভাবনা কোমলভাবে উল্লেখ করতে পারো।
""",

    "crisis": """
জরুরি নিরাপত্তা নির্দেশ:

ব্যবহারকারীর কথায় আত্মহানি বা আত্মহত্যার
ঝুঁকির ইঙ্গিত রয়েছে।

শান্ত ও আন্তরিকভাবে উত্তর দাও।
তার নিরাপত্তা সম্পর্কে সরাসরি জিজ্ঞাসা করো।
সে কি এখন নিজেকে আঘাত করার কথা ভাবছে?
সে কি এই মুহূর্তে নিরাপদ স্থানে আছে?

এখনই কাছের বিশ্বস্ত কাউকে জানাতে এবং
একা না থাকতে উৎসাহিত করো।

তাৎক্ষণিক বিপদ হলে বাংলাদেশে ৯৯৯-এ কল
করতে অথবা নিকটস্থ হাসপাতালে যেতে বলো।

কোনো পদ্ধতি বা আত্মহানির উপায় বলবে না।
"""
}


# ============================================================
# CONVERSATION MEMORY
# ============================================================

@lru_cache(maxsize=64)
def _summarize(transcript: str) -> str:

    llm = get_llm(temperature=0.2)

    messages = [
        SystemMessage(
            content="""
নিচের কথোপকথনটি ৬-৮ লাইনে সংক্ষেপ করো।

রাখবে:
- ব্যবহারকারীর মূল সমস্যা।
- মন খারাপের সম্ভাব্য কারণ।
- গুরুত্বপূর্ণ ঘটনা।
- Positive ও negative mood changes।
- আগে কী সাহায্য করেছে।
- কী সাহায্য করেনি।
- দীর্ঘস্থায়ী কষ্ট বা ঝুঁকির ইঙ্গিত।

ব্যবহারকারীর কথা বানিয়ে লিখবে না।
শুধু সারাংশ দেবে।
"""
        ),
        HumanMessage(content=transcript)
    ]

    result = llm.invoke(messages).content

    return result


def _split_history(history):

    cut = max(
        0,
        ((len(history) - RECENT_WINDOW) // SUMMARY_STEP)
        * SUMMARY_STEP
    )

    return history[:cut], history[cut:]


# ============================================================
# MAIN CHAT FUNCTION
# ============================================================

def get_chat_response(
    history,
    message,
    user_name="",
    mood_context=""
):

    # ----------------------------------------
    # 1. Previous user messages
    # ----------------------------------------

    recent_user_messages = [
        m["content"]
        for m in history
        if m["role"] == "user"
    ]

    # ----------------------------------------
    # 2. Detect mood
    # ----------------------------------------

    mood_level = detect_mood_level(
        message=message,
        recent_user_messages=recent_user_messages,
        mood_context=mood_context
    )

    # ----------------------------------------
    # 3. Select LLM temperature
    # ----------------------------------------

    temperature = (
        0.2 if mood_level == "crisis"
        else 0.5 if mood_level in (
            "low",
            "negative",
            "persistent_low",
            "depression_related"
        )
        else 0.65
    )

    llm = get_llm(temperature=temperature)

    # ----------------------------------------
    # 4. Build system prompt
    # ----------------------------------------

    system_text = SYSTEM_PROMPT

    if user_name:
        system_text += f"\n\nব্যবহারকারীর নাম: {user_name}"

    # ----------------------------------------
    # 5. Add Dialect Lab context
    # ----------------------------------------

    if mood_context:

        system_text += (
            "\n\nসাম্প্রতিক Dialect Lab Analysis:\n"
            f"{mood_context}\n"
            "এটি সহায়ক context হিসেবে ব্যবহার করবে। "
            "নিজে থেকে নতুন তথ্য বানাবে না।"
        )

    # ----------------------------------------
    # 6. Add conversation summary
    # ----------------------------------------

    older, recent = _split_history(history)

    if older:

        transcript = "\n".join(
            f'{"User" if m["role"] == "user" else "Assistant"}: '
            f'{m["content"]}'
            for m in older
        )

        try:

            summary = _summarize(transcript)

            system_text += (
                "\n\nআগের কথোপকথনের সারাংশ:\n"
                f"{summary}"
            )

        except Exception as error:

            print("Summary error:", error)

    # ----------------------------------------
    # 7. Add mood-specific directive
    # ----------------------------------------

    directive = MOOD_DIRECTIVES.get(
        mood_level,
        ""
    )

    if directive:
        system_text += "\n\n" + directive

    # ----------------------------------------
    # 8. Build conversation messages
    # ----------------------------------------

    messages = [
        SystemMessage(content=system_text)
    ]

    for item in recent:

        if item["role"] == "user":

            messages.append(
                HumanMessage(content=item["content"])
            )

        elif item["role"] == "assistant":

            messages.append(
                AIMessage(content=item["content"])
            )

    messages.append(
        HumanMessage(content=message)
    )

    # ----------------------------------------
    # 9. Generate response
    # ----------------------------------------

    response = llm.invoke(messages)

    return response.content
