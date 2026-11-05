
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

NEGATIVE_THRESHOLD = 0.40


# ============================================================
# MOOD KEYWORDS
# ============================================================

LOW_MOOD_KEYWORDS = [
    "মন খারাপ", "ভালো লাগছে না", "ভালো লাগে না",
    "কষ্ট হচ্ছে", "অনেক কষ্ট", "একাকী লাগছে",
    "একা লাগছে", "হতাশ", "হতাশ লাগছে",
    "কান্না পাচ্ছে", "কাঁদতে ইচ্ছা করছে",
    "চিন্তা হচ্ছে", "টেনশন হচ্ছে",
    "কিছু ভালো লাগছে না", "বিরক্ত লাগছে",
    "মেজাজ খারাপ", "ভেঙে পড়েছি",
    "ক্লান্ত লাগছে", "কিছু করতে ইচ্ছা করছে না",
    "মনে শান্তি নেই", "ভালো নেই"
]

POSITIVE_KEYWORDS = [
    "ভালো আছি", "অনেক ভালো", "খুশি",
    "আনন্দ লাগছে", "মজা লাগছে",
    "সুন্দর লাগছে", "ভালো লাগছে",
    "সফল হয়েছি", "সফল হলাম",
    "অনেক খুশি", "দারুণ লাগছে",
    "আলহামদুলিল্লাহ ভালো"
]

CRISIS_KEYWORDS = [
    "আত্মহত্যা করতে চাই",
    "আত্মহত্যা করব",
    "নিজেকে মেরে ফেলতে চাই",
    "নিজেকে শেষ করে দিতে চাই",
    "বেঁচে থাকতে চাই না",
    "আর বাঁচতে চাই না",
    "মরে যেতে চাই",
    "মরে গেলেই ভালো",
    "জীবন শেষ করে দিতে চাই",
    "নিজের ক্ষতি করতে চাই",
    "নিজেকে আঘাত করতে চাই",
    "suicide",
    "kill myself",
    "end my life",
    "want to die",
    "don't want to live",
    "hurt myself"
]


# ============================================================
# ADVICE INTENT KEYWORDS
# ============================================================

ADVICE_KEYWORDS = [
    "কি করব", "কী করব", "কী করা উচিত",
    "পরামর্শ দাও", "পরামর্শ চাই",
    "সমাধান কী", "সমাধান দাও",
    "কিভাবে সমাধান করব", "কীভাবে সমাধান করব",
    "help me", "give me advice",
    "what should i do", "suggestion",
    "কোনো উপায় আছে", "উপায় বলো"
]


# ============================================================
# PROBLEM CATEGORY KEYWORDS
# ============================================================

PROBLEM_KEYWORDS = {
    "study": [
        "পড়াশোনা", "পরীক্ষা", "রেজাল্ট",
        "পড়তে পারছি না", "পড়াশোনায় মন বসে না",
        "study", "exam", "result", "academic"
    ],

    "relationship": [
        "প্রেম", "ভালোবাসা", "ব্রেকআপ",
        "সম্পর্ক", "রিলেশন", "প্রেমিকা",
        "প্রেমিক", "relationship", "breakup",
        "girlfriend", "boyfriend"
    ],

    "loneliness": [
        "একা", "একাকী", "কেউ নেই",
        "কথা বলার কেউ নেই", "lonely",
        "alone", "loneliness"
    ],

    "family": [
        "পরিবার", "বাবা", "মা",
        "বাড়িতে সমস্যা", "পরিবারের সমস্যা",
        "family", "parents"
    ],

    "career": [
        "চাকরি", "ক্যারিয়ার", "ভবিষ্যৎ",
        "বেকার", "ইন্টারভিউ", "career",
        "job", "unemployed", "future"
    ],

    "overthinking": [
        "অতিরিক্ত চিন্তা", "বেশি চিন্তা",
        "বারবার ভাবি", "overthinking",
        "অনেক ভাবি", "মাথায় চিন্তা"
    ],

    "stress": [
        "চাপ", "মানসিক চাপ", "টেনশন",
        "স্ট্রেস", "stress", "pressure",
        "anxiety", "anxious"
    ],

    "motivation": [
        "ইচ্ছা করে না", "কিছু করতে চাই না",
        "অনুপ্রেরণা", "মোটিভেশন",
        "motivation", "unmotivated"
    ]
}


# ============================================================
# DIALECT KEYWORDS
# Note: Some words overlap across regions.
# Detection is heuristic, not a scientific dialect classifier.
# ============================================================

DIALECT_KEYWORDS = {

    "dinajpur": [
        "ক্যাংকা", "ক্যানে", "আইজক্যা",
        "কইরবার", "আসচিল", "অইছে",
        "হইছে", "নাগে", "নাগোছে",
        "মুই", "মোর", "হামার",
        "এ্যাংকা", "গরমোত", "চ্যাংড়া",
        "চেংড়ী", "অংগের", "আইসা"
    ],

    "rangpur": [
        "মুই", "মোর", "হামার",
        "হামরা", "ক্যানে", "কই",
        "কইরছি", "গেইছে", "যাম",
        "খাম", "মোক", "তোক",
        "তোরে", "কিবা", "কুনো",
        "নাই", "অ্যালা", "আইজ"
    ],

    "standard": [
        "আমি", "আমার", "তুমি", "আপনি",
        "কেন", "কীভাবে", "কিভাবে",
        "করছি", "করব", "যাচ্ছি",
        "খাচ্ছি", "ভালো", "খারাপ",
        "হয়েছে", "হচ্ছে", "আছি"
    ]
}


# ============================================================
# BANGLISH MARKERS
# ============================================================

BANGLISH_MARKERS = [
    "ami", "amar", "amr", "tumi",
    "tomar", "apni", "kemon",
    "valo", "bhalo", "kharap",
    "mon", "nai", "mone", "ki",
    "kivabe", "korbo", "korchi",
    "achi", "acchi", "bujhi",
    "bujhlam", "kosto", "bhalo",
    "lagche", "lagena"
]


# ============================================================
# TEXT UTILITIES
# ============================================================

def normalize_text(text):
    """Normalize user text for keyword matching."""

    if not text:
        return ""

    text = str(text).lower().strip()
    text = re.sub(r"\s+", " ", text)

    return text


def contains_any(text, keywords):
    """Check whether any keyword exists in text."""

    text = normalize_text(text)

    return any(
        keyword.lower() in text
        for keyword in keywords
    )


def get_message_content(message):
    """Extract content from history message."""

    if isinstance(message, dict):
        return str(message.get("content", ""))

    if isinstance(message, (HumanMessage, AIMessage)):
        return str(message.content)

    return str(message)


def get_user_messages(history):
    """Return only user messages from history."""

    user_messages = []

    for item in history or []:

        if isinstance(item, dict):

            role = item.get("role", "")

            if role in ["user", "human"]:
                user_messages.append(
                    str(item.get("content", ""))
                )

        elif isinstance(item, HumanMessage):

            user_messages.append(
                str(item.content)
            )

    return user_messages


# ============================================================
# DIALECT DETECTION
# ============================================================

def detect_dialect(message, history=None):
    """
    Detect:
    - dinajpur
    - rangpur
    - standard
    - banglish
    - english

    Uses current message first and recent user messages
    as supporting context.

    When uncertain, defaults to Standard Bangla.
    """

    text = normalize_text(message)

    if not text:
        return "standard"

    bangla_pattern = re.compile(r"[\u0980-\u09FF]")

    has_bangla = bool(bangla_pattern.search(text))

    # --------------------------------------------------------
    # English / Banglish detection
    # --------------------------------------------------------

    if not has_bangla:

        words = re.findall(r"[a-zA-Z]+", text)

        if not words:
            return "standard"

        banglish_score = sum(
            1 for word in words
            if word in BANGLISH_MARKERS
        )

        if banglish_score >= 1:
            return "banglish"

        return "english"

    # --------------------------------------------------------
    # Current message dialect scoring
    # --------------------------------------------------------

    scores = {
        "dinajpur": 0,
        "rangpur": 0,
        "standard": 0
    }

    for dialect, keywords in DIALECT_KEYWORDS.items():

        for keyword in keywords:

            if keyword in text:
                scores[dialect] += 1

    # --------------------------------------------------------
    # Recent user messages provide small supporting evidence
    # --------------------------------------------------------

    recent_messages = get_user_messages(history)[-6:]

    for old_message in recent_messages:

        old_text = normalize_text(old_message)

        for dialect, keywords in DIALECT_KEYWORDS.items():

            for keyword in keywords:

                if keyword in old_text:
                    scores[dialect] += 0.25

    # --------------------------------------------------------
    # Conservative decision
    # --------------------------------------------------------

    regional_scores = {
        "dinajpur": scores["dinajpur"],
        "rangpur": scores["rangpur"]
    }

    best_regional = max(
        regional_scores,
        key=regional_scores.get
    )

    regional_score = regional_scores[best_regional]

    other_regional = (
        "rangpur"
        if best_regional == "dinajpur"
        else "dinajpur"
    )

    difference = (
        regional_score -
        regional_scores[other_regional]
    )

    if regional_score >= 1 and difference >= 1:
        return best_regional

    # If no clear regional evidence, use Standard Bangla.
    return "standard"


# ============================================================
# DIALECT RESPONSE INSTRUCTIONS
# ============================================================

DIALECT_DIRECTIVES = {

    "dinajpur": """
The user is communicating in the Dinajpur regional dialect.

Response rules:
- Reply naturally in Dinajpur-style Bangla when confident.
- Use familiar regional expressions naturally.
- Do not exaggerate dialect words.
- Maintain respectful and friendly language.
- Avoid using rude or overly informal pronouns.
- If a regional expression is uncertain, use clear Standard Bangla.
""",

    "rangpur": """
The user is communicating in the Rangpur regional dialect.

Response rules:
- Reply naturally in Rangpur-style Bangla when confident.
- Use familiar Rangpur regional expressions naturally.
- Do not exaggerate dialect words.
- Maintain respectful and friendly language.
- Avoid using rude or overly informal pronouns.
- If a regional expression is uncertain, use clear Standard Bangla.
""",

    "standard": """
The user is communicating in Standard Bangla.

Response rules:
- Reply in natural Standard Bangla.
- Use simple, clear and friendly language.
- Avoid unnecessary regional dialect expressions.
""",

    "banglish": """
The user is communicating in Banglish (Romanized Bangla).

Response rules:
- Reply in Banglish using English/Roman letters.
- Keep the language natural and easy to understand.
- Do not switch to Bengali script unless the user does.
""",

    "english": """
The user is communicating in English.

Response rules:
- Reply in natural, simple English.
- Do not switch to Bangla unless the user does.
"""
}


# ============================================================
# MOOD DETECTION
# ============================================================

def detect_mood_level(message):
    """
    Detect a basic mood signal from the current message.

    Returns:
    - crisis
    - low
    - positive
    - neutral

    This is keyword-based and is not a clinical risk assessment.
    """

    text = normalize_text(message)

    # Crisis signal gets priority.
    if contains_any(text, CRISIS_KEYWORDS):
        return "crisis"

    if contains_any(text, LOW_MOOD_KEYWORDS):
        return "low"

    if contains_any(text, POSITIVE_KEYWORDS):
        return "positive"

    return "neutral"


# ============================================================
# ADVICE INTENT DETECTION
# ============================================================

def wants_advice(message):

    return contains_any(
        message,
        ADVICE_KEYWORDS
    )


# ============================================================
# PROBLEM CATEGORY DETECTION
# ============================================================

def detect_problem_category(message):

    text = normalize_text(message)

    for category, keywords in PROBLEM_KEYWORDS.items():

        if contains_any(text, keywords):
            return category

    return "general"


# ============================================================
# MOOD CONTEXT
# ============================================================

def get_mood_context_message(mood_context):

    if not mood_context:
        return ""

    return f"""
Additional mood analysis context from the application:

{mood_context}

Use this information carefully.
Do not treat sentiment scores as a medical diagnosis.
Do not assume that a negative sentiment score proves depression.
"""


# ============================================================
# SYSTEM PROMPT
# ============================================================

SYSTEM_PROMPT = """
You are a supportive AI Mood Companion for a Bangla dialect-based
sentiment analysis application.

Your purpose is to:
1. Listen to the user's feelings.
2. Understand their emotional situation.
3. Respond with empathy and kindness.
4. Provide practical and realistic suggestions when appropriate.
5. Maintain a friendly and non-judgmental conversation.

GENERAL RULES:

- First understand what the user is saying.
- Do not judge, blame, shame, or criticize the user.
- Do not give generic motivational replies every time.
- Avoid repeating the same advice.
- Ask one relevant follow-up question when useful.
- Keep answers conversational and understandable.
- Do not claim to be a human therapist or doctor.
- Never diagnose depression or any mental health condition.
- Never prescribe medication.
- Do not pretend that sentiment analysis can diagnose a person.
- Respect the user's language and dialect.

EMOTIONAL SUPPORT:

If the user feels sad:
- Acknowledge their feelings.
- Let them express themselves.
- Avoid saying that their problem is insignificant.
- Suggest small, realistic steps when appropriate.

IF THE USER ASKS FOR ADVICE:

- Understand the actual problem first.
- Give specific and practical suggestions.
- Avoid unrealistic promises.
- Do not force the user to follow your suggestions.

SAFETY:

If the user mentions suicide, self-harm, or immediate danger:
- Treat the situation seriously.
- Do not provide methods or instructions for self-harm.
- Do not respond with ordinary motivation or jokes.
- Encourage immediate support from a trusted person.
- Encourage moving away from anything they could use to hurt themselves.
- If danger is immediate, encourage emergency services or the nearest hospital.
- Ask directly whether they are in immediate danger or have already harmed themselves.
"""


# ============================================================
# MOOD IMPROVEMENT PROMPT
# ============================================================

MOOD_IMPROVEMENT_PROMPT = """
When the user expresses low mood or emotional distress:

1. First acknowledge their feelings.
2. Show empathy without judging them.
3. Avoid forcing positivity.
4. Suggest one or two small actions that may help.
5. Encourage talking to someone they trust.
6. Ask a gentle question to understand their situation.

Examples of helpful suggestions:
- Take a short break.
- Drink some water.
- Take a slow walk if comfortable.
- Talk to a trusted friend or family member.
- Break a difficult task into smaller steps.
- Take some rest if tired.

Do not present these suggestions as a cure.
"""


# ============================================================
# PROBLEM-SPECIFIC GUIDANCE
# ============================================================

PROBLEM_GUIDANCE = {

    "study": """
For study-related problems:
- Help the user break tasks into small parts.
- Suggest a realistic study routine.
- Avoid creating additional pressure.
- Encourage short breaks.
""",

    "relationship": """
For relationship problems:
- Listen without judging either person.
- Encourage healthy communication and boundaries.
- Do not make assumptions about the other person's intentions.
""",

    "loneliness": """
For loneliness:
- Acknowledge that loneliness can be difficult.
- Encourage connecting with a trusted person.
- Suggest small social interactions when appropriate.
""",

    "family": """
For family problems:
- Listen carefully.
- Avoid blaming family members without context.
- Encourage safe and respectful communication.
""",

    "career": """
For career problems:
- Help identify the actual concern.
- Break career goals into manageable steps.
- Avoid promising guaranteed success.
""",

    "overthinking": """
For overthinking:
- Help separate facts from assumptions.
- Suggest writing down worries.
- Focus on one manageable next step.
""",

    "stress": """
For stress:
- Encourage a short break and slow breathing.
- Help identify the main source of pressure.
- Suggest realistic ways to reduce workload.
""",

    "motivation": """
For motivation problems:
- Avoid blaming the user for low motivation.
- Suggest starting with a very small task.
- Recognize small progress.
""",

    "general": """
For general problems:
- Listen carefully.
- Ask a clarifying question when necessary.
- Give practical and empathetic support.
"""
}


# ============================================================
# CRISIS RESPONSE
# ============================================================

def get_crisis_response(dialect="standard"):
    """
    Fixed safety response.

    Crisis situations bypass the normal LLM response so that
    the application can provide consistent safety guidance.
    """

    responses = {

        "standard": """
তোমার কথাগুলো আমি গুরুত্ব দিয়ে শুনছি। তুমি যে কষ্টের মধ্যে দিয়ে যাচ্ছ,
সেটা একা সামলাতে হবে না। তোমার নিরাপত্তা এখন সবচেয়ে গুরুত্বপূর্ণ।

আমি তোমাকে বিচার করছি না। তোমার সঙ্গে কথা বলতে আমি এখানে আছি।

আমি তোমাকে সরাসরি দুটি বিষয় জিজ্ঞেস করতে চাই:

১. তুমি কি এই মুহূর্তে নিজেকে আঘাত করার বা আত্মহত্যা করার কথা ভাবছ?
২. তুমি কি ইতিমধ্যে নিজেকে আঘাত করেছ, অথবা এমন কোনো পরিকল্পনা বা উপায় তোমার কাছে আছে?

দয়া করে এখনই একা থেকো না। বিশ্বাসযোগ্য কোনো বন্ধু, পরিবারের সদস্য
বা কাছের মানুষের সঙ্গে যোগাযোগ করো এবং তাকে তোমার বর্তমান অবস্থার কথা বলো।

নিজেকে আঘাত করার মতো কোনো জিনিস কাছে থাকলে সেগুলো থেকে দূরে সরে যাও
এবং সম্ভব হলে অন্য কারও সঙ্গে নিরাপদ জায়গায় থাকো।

যদি মনে হয় তুমি এখনই নিজেকে আঘাত করতে পারো, তাহলে বাংলাদেশে জরুরি
সেবা ৯৯৯-এ কল করো অথবা নিকটস্থ হাসপাতালের জরুরি বিভাগে যাও।

তুমি চাইলে আমাকে বলতে পারো—এই মুহূর্তে তুমি কি নিরাপদে আছ?
""",

        "dinajpur": """
তোমার কথাগুলা আমি গুরুত্ব দিয়া শুনছি। তুমি যে কষ্টের মধ্যে আছ,
সেইটা একা সামলানোর দরকার নাই। তোমার নিরাপত্তা এখন সবচেয়ে জরুরি।

আমি তোমাকে বিচার করতেছি না। তোমার কথা শুনবার জন্য আমি আছি।

আমি তোমাকে দুইটা কথা জিজ্ঞেস করবার চাই:

১. তুমি কি এখন নিজের ক্ষতি করবার বা আত্মহত্যা করবার কথা ভাবতেছ?
২. তুমি কি ইতিমধ্যে নিজের কোনো ক্ষতি করছ, অথবা এখনই এমন কিছু করবার
পরিকল্পনা আছে?

দয়া করে এখন একা থেকো না। বিশ্বাসযোগ্য কোনো বন্ধু, পরিবারের মানুষ
বা কাছের কারও সঙ্গে যোগাযোগ করো।

নিজের ক্ষতি করবার মতো কিছু কাছে থাকলে সেইগুলা থেকে দূরে সরে যাও।
সম্ভব হলে অন্য কারও সঙ্গে নিরাপদ জায়গায় থাকো।

যদি মনে হয় এখনই নিজের ক্ষতি করবার আশঙ্কা আছে, বাংলাদেশে ৯৯৯-এ কল করো
অথবা কাছের হাসপাতালের জরুরি বিভাগে যাও।

তুমি কি এই মুহূর্তে নিরাপদে আছ?
""",

        "rangpur": """
তোমার কথাগুলা আমি মন দিয়া শুনতেছি। তুমি যে কষ্টের মধ্যে আছ,
সেইটা একা সামলানো লাগবে না। তোমার নিরাপত্তা এখন সবচেয়ে জরুরি।

আমি তোমাকে বিচার করতেছি না। তোমার কথা শুনবার জন্য আছি।

আমি দুইটা কথা জিজ্ঞেস করি:

১. তুমি কি এখন নিজের ক্ষতি করার বা আত্মহত্যা করার কথা ভাবতেছ?
২. তুমি কি ইতিমধ্যে নিজের ক্ষতি করছ, অথবা এখনই কিছু করার পরিকল্পনা আছে?

দয়া করে একা থেকো না। বিশ্বাসযোগ্য বন্ধু, পরিবারের মানুষ
বা কাছের কারও সঙ্গে এখনই কথা কও।

নিজের ক্ষতি করার মতো কিছু কাছে থাকলে সেগুলা থেকে দূরে যাও।
সম্ভব হলে অন্য কারও সঙ্গে নিরাপদ জায়গায় থাকো।

যদি এখনই নিজের ক্ষতি করার ভয় থাকে, বাংলাদেশে ৯৯৯-এ কল দাও
অথবা নিকটস্থ হাসপাতালের জরুরি বিভাগে যাও।

তুমি কি এখন নিরাপদে আছ?
""",

        "banglish": """
Tomar kothagulo ami seriously nicchi. Tumi je koshtor moddhe
acho, seta eka handle korte hobe na. Tomar safety ekhon
sobcheye important.

Ami tomake judge korchi na. Ami tomar kotha shunte ekhane achi.

Ami tomake duita question korte chai:

1. Tumi ki ekhon nijer khoti korar ba suicide korar kotha vabcho?
2. Tumi ki already nijer kono khoti korecho, ba ekhon kichu
korar plan ache?

Please ekhon eka theko na. Trusted friend, family member
ba kacher kono manusher sathe contact koro.

Nijer khoti korar moto kichu kache thakle segulo theke dure sore jao.
Possible hole onno karo sathe safe place-e thako.

Jodi mone hoy tumi ekhoni nijer khoti korte paro,
Bangladesh-e 999 call koro othoba nearest hospital-er
emergency department-e jao.

Tumi ki ekhon safe acho?
""",

        "english": """
I'm taking what you're saying seriously. You do not have to
handle this pain alone. Your safety is the most important thing
right now.

I'm not here to judge you. I'm here to listen.

Can I ask you two direct questions?

1. Are you thinking about hurting yourself or ending your life right now?
2. Have you already hurt yourself, or do you have a plan to do so?

Please do not stay alone right now. Contact someone you trust,
such as a friend, family member, or someone nearby.

Move away from anything you could use to hurt yourself.
If possible, stay somewhere safe with another person.

If you may act on these thoughts or are in immediate danger,
call Bangladesh emergency services at 999 or go to the nearest
hospital emergency department.

Are you safe right now?
"""
    }

    return responses.get(
        dialect,
        responses["standard"]
    )


# ============================================================
# CRISIS CONTEXT CHECK
# ============================================================

def has_recent_crisis_context(history):
    """
    Checks whether recent conversation contained a crisis signal.

    This helps retain safety awareness when the user replies
    with short messages such as 'yes' or 'no'.
    """

    recent_user_messages = get_user_messages(history)[-4:]

    return any(
        contains_any(message, CRISIS_KEYWORDS)
        for message in recent_user_messages
    )


# ============================================================
# LLM OUTPUT EXTRACTION
# ============================================================

def extract_response_content(response):

    content = getattr(response, "content", response)

    if isinstance(content, list):

        content = "".join(
            item.get("text", "")
            if isinstance(item, dict)
            else str(item)
            for item in content
        )

    return str(content).strip()


# ============================================================
# CONVERSATION SUMMARIZATION
# ============================================================

def _split_history(history, chunk_size=SUMMARY_STEP):

    chunks = []

    for index in range(0, len(history), chunk_size):

        chunks.append(
            history[index:index + chunk_size]
        )

    return chunks


@lru_cache(maxsize=64)
def _summarize(text):
    """
    Summarize older conversation history.
    Cached to reduce repeated LLM calls.
    """

    if not text.strip():
        return ""

    try:

        llm = get_llm(temperature=0.2)

        messages = [
            SystemMessage(
                content="""
You are a conversation summarizer.

Summarize the conversation while preserving:
- User's important concerns
- Emotional context
- Important events
- Previously discussed problems
- Suggestions already provided
- Relevant preferences

Do not invent information.
Do not diagnose the user.
Keep the summary concise.
"""
            ),

            HumanMessage(
                content=f"""
Summarize this conversation:

{text}
"""
            )
        ]

        response = llm.invoke(messages)

        return extract_response_content(response)

    except Exception as error:

        print("Summary error:", error)

        return ""


def build_conversation_summary(history):
    """
    Summarize old conversation messages while keeping
    recent messages unchanged.
    """

    if not history:
        return ""

    if len(history) <= RECENT_WINDOW:
        return ""

    old_history = history[:-RECENT_WINDOW]

    chunks = _split_history(old_history)

    summaries = []

    for chunk in chunks:

        conversation_text = ""

        for item in chunk:

            if isinstance(item, dict):

                role = item.get("role", "user")
                content = item.get("content", "")

            else:

                role = (
                    "assistant"
                    if isinstance(item, AIMessage)
                    else "user"
                )

                content = get_message_content(item)

            conversation_text += (
                f"{role}: {content}\n"
            )

        summary = _summarize(conversation_text)

        if summary:
            summaries.append(summary)

    return "\n".join(summaries)


# ============================================================
# HISTORY CONVERSION
# ============================================================

def convert_history_to_messages(history):
    """
    Convert application history dictionaries into LangChain messages.
    """

    messages = []

    for item in history or []:

        if isinstance(item, (HumanMessage, AIMessage)):
            messages.append(item)
            continue

        if not isinstance(item, dict):
            continue

        role = item.get("role", "")
        content = str(item.get("content", ""))

        if role in ["user", "human"]:

            messages.append(
                HumanMessage(content=content)
            )

        elif role in ["assistant", "ai"]:

            messages.append(
                AIMessage(content=content)
            )

    return messages


# ============================================================
# MAIN CHAT FUNCTION
# ============================================================

def get_chat_response(
    history,
    message,
    user_name="",
    mood_context=""
):
    """
    Main chatbot function.

    Parameters:
        history: previous chat messages
        message: current user message
        user_name: optional user name
        mood_context: sentiment analysis context

    Returns:
        AI response as string
    """

    message = str(message).strip()

    if not message:
        return "তোমার কথাটা একটু বিস্তারিত বলবে?"

    # --------------------------------------------------------
    # 1. Detect dialect
    # --------------------------------------------------------

    detected_dialect = detect_dialect(
        message=message,
        history=history
    )

    # --------------------------------------------------------
    # 2. Detect mood
    # --------------------------------------------------------

    mood_level = detect_mood_level(message)

    # --------------------------------------------------------
    # 3. Detect advice intent
    # --------------------------------------------------------

    advice_requested = wants_advice(message)

    # --------------------------------------------------------
    # 4. Detect problem category
    # --------------------------------------------------------

    problem_category = detect_problem_category(message)

    # --------------------------------------------------------
    # 5. Crisis handling
    # --------------------------------------------------------

    if mood_level == "crisis":

        return get_crisis_response(
            detected_dialect
        )

    # --------------------------------------------------------
    # 6. Build system prompt
    # --------------------------------------------------------

    system_text = SYSTEM_PROMPT

    # Add dialect instruction.
    system_text += "\n\n"

    system_text += DIALECT_DIRECTIVES.get(
        detected_dialect,
        DIALECT_DIRECTIVES["standard"]
    )

    # Add user name if available.
    if user_name:

        system_text += f"""

The user's preferred name is {user_name}.
Use their name naturally when appropriate.
Do not overuse it.
"""

    # Add mood improvement instruction.
    if mood_level == "low":

        system_text += "\n\n"
        system_text += MOOD_IMPROVEMENT_PROMPT

    # Add advice instruction.
    if advice_requested:

        system_text += """

The user appears to be asking for advice.
Provide specific, practical and empathetic suggestions.
Do not overwhelm the user with too many steps.
"""

    # Add problem-specific instruction.
    system_text += "\n\n"

    system_text += PROBLEM_GUIDANCE.get(
        problem_category,
        PROBLEM_GUIDANCE["general"]
    )

    # Add sentiment context.
    context_text = get_mood_context_message(
        mood_context
    )

    if context_text:

        system_text += "\n\n"
        system_text += context_text

    # --------------------------------------------------------
    # 7. Build conversation summary
    # --------------------------------------------------------

    conversation_summary = build_conversation_summary(
        history
    )

    if conversation_summary:

        system_text += f"""

Previous conversation summary:

{conversation_summary}

Use this summary to maintain continuity.
Do not repeat old advice unnecessarily.
"""

    # --------------------------------------------------------
    # 8. Prepare LLM messages
    # --------------------------------------------------------

    messages = [
        SystemMessage(content=system_text)
    ]

    recent_history = (history or [])[-RECENT_WINDOW:]

    messages.extend(
        convert_history_to_messages(recent_history)
    )

    # Avoid adding the current user message twice
    # if it is already the last item in history.
    already_in_history = False

    if history:

        last_item = history[-1]

        if isinstance(last_item, dict):

            already_in_history = (
                last_item.get("role") in ["user", "human"]
                and str(last_item.get("content", "")).strip()
                == message
            )

        elif isinstance(last_item, HumanMessage):

            already_in_history = (
                str(last_item.content).strip() == message
            )

    if not already_in_history:

        messages.append(
            HumanMessage(content=message)
        )

    # --------------------------------------------------------
    # 9. Call LLM
    # --------------------------------------------------------

    try:

        llm = get_llm(temperature=0.65)

        response = llm.invoke(messages)

        return extract_response_content(response)

    except Exception as error:

        print("Chatbot error:", error)

        fallback_responses = {

            "standard":
                "দুঃখিত, এই মুহূর্তে উত্তর দিতে একটু সমস্যা হচ্ছে। "
                "তুমি আবার একটু পরে চেষ্টা করবে?",

            "dinajpur":
                "দুঃখিত, এই মুহূর্তে উত্তর দিতে একটু সমস্যা হইতেছে। "
                "একটু পরে আবার চেষ্টা করবা?",

            "rangpur":
                "দুঃখিত, এখন উত্তর দিতে একটু সমস্যা হইতেছে। "
                "একটু পরে আবার চেষ্টা করবা?",

            "banglish":
                "Sorry, ekhon response dite problem hocche. "
                "Ektu pore abar try koro?",

            "english":
                "Sorry, I'm having trouble responding right now. "
                "Please try again in a little while."
        }

        return fallback_responses.get(
            detected_dialect,
            fallback_responses["standard"]
        )
