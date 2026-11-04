
# import streamlit as st
# import pandas as pd
# import plotly.express as px

# from database import init_db, save_analysis, get_history
# from auth import auth_page
# from dialect_service import identify_dialect
# from sentiment_service import analyze_sentiment
# from chatbot_service import get_chat_response


# # PAGE CONFIGURATION
# st.set_page_config(
#     page_title="DialectMood AI",
#     page_icon="🌿",
#     layout="wide"
# )


# # CUSTOM CSS
# st.markdown("""
# <style>
# @import url('https://fonts.googleapis.com/css2?family=Hind+Siliguri:wght@400;500;600;700;800&display=swap');

# html, body, [class*="css"] {
#     font-family: 'Hind Siliguri', sans-serif;
# }

# .stApp {
#     background-color: #F5FAF6;
# }

# .main-title {
#     color: #267653;
#     font-size: 30px;
#     font-weight: 800;
#     margin-bottom: 5px;
# }

# .hero {
#     background: linear-gradient(120deg, #174B36 0%, #4B9873 100%);
#     padding: 45px;
#     border-radius: 20px;
#     color: #FFFFFF;
#     width: 100%;
#     box-sizing: border-box;
#     margin: 15px 0 25px 0;
#     box-shadow: 0 8px 25px rgba(23, 75, 54, 0.15);
# }

# .hero h1 {
#     color: #FFFFFF !important;
#     font-size: clamp(26px, 4vw, 42px);
#     font-weight: 800;
#     line-height: 1.3;
#     margin: 0 0 8px 0;
#     padding: 0;
# }

# .hero p {
#     color: #E7F5EC !important;
#     font-size: 17px;
#     line-height: 1.8;
#     margin: 18px 0 0 0;
#     max-width: 650px;
# }

# @media screen and (max-width: 768px) {
#     .hero {
#         padding: 25px 20px;
#         border-radius: 15px;
#     }

#     .hero p {
#         font-size: 15px;
#     }

#     .main-title {
#         font-size: 25px;
#     }
# }
# </style>
# """, unsafe_allow_html=True)


# # INITIALIZATION
# init_db()

# if "user" not in st.session_state:
#     st.session_state.user = None

# if "page" not in st.session_state:
#     st.session_state.page = "Home"

# if "chat_history" not in st.session_state:
#     st.session_state.chat_history = []

# if "last_analysis" not in st.session_state:
#     st.session_state.last_analysis = None


# # AUTHENTICATION
# if st.session_state.user is None:
#     auth_page()
#     st.stop()


# # NAVBAR
# st.markdown(
#     '<div class="main-title">🌿 DialectMood AI</div>',
#     unsafe_allow_html=True
# )

# st.caption("Your Bangla Dialect Intelligence & Mood Companion")

# pages = ["Home", "Dialect Lab", "Mood Chat", "My Journal"]

# columns = st.columns(4)

# for col, page in zip(columns, pages):
#     with col:
#         if st.button(
#             page,
#             use_container_width=True,
#             type="primary" if st.session_state.page == page else "secondary"
#         ):
#             st.session_state.page = page
#             st.rerun()

# st.divider()

# st.write(f"Welcome back, **{st.session_state.user['name']}** 🌿")


# # HOME
# if st.session_state.page == "Home":

#     st.markdown("""
#     <div class="hero">
#         <h1>Understand Your Dialect.</h1>
#         <h1>Understand Your Emotions.</h1>
#         <p>
#             Explore Dinajpur and Rangpur dialects,
#             discover emotional expressions and talk
#             with your AI mood companion.
#         </p>
#     </div>
#     """, unsafe_allow_html=True)

#     st.write("")

#     c1, c2, c3 = st.columns(3)

#     c1.metric("Regional Dialects", "2+")
#     c2.metric("Sentiment Classes", "4")
#     c3.metric("AI Companion", "Active")

#     st.subheader("Explore your AI platform")

#     a, b = st.columns(2)

#     with a:
#         if st.button("🧭 Explore Dialect Lab", use_container_width=True):
#             st.session_state.page = "Dialect Lab"
#             st.rerun()

#     with b:
#         if st.button("💚 Talk to Mood Companion", use_container_width=True):
#             st.session_state.page = "Mood Chat"
#             st.rerun()


# # DIALECT LAB
# elif st.session_state.page == "Dialect Lab":

#     st.header("🧭 Dialect & Sentiment Analysis")

#     st.write(
#         "Write a Bangla sentence to analyze its dialect and emotion."
#     )

#     text = st.text_area(
#         "Enter your text",
#         height=150,
#         placeholder="মুই আজকে খুব ভালো আছি..."
#     )

#     if st.button(
#         "Analyze Text",
#         type="primary",
#         disabled=not text.strip()
#     ):

#         try:
#             with st.spinner("Analyzing dialect and sentiment..."):

#                 dialect = identify_dialect(text)
#                 sentiment = analyze_sentiment(text)

#             explanation = (
#                 dialect.get("explanation", "")
#                 + " "
#                 + sentiment.get("explanation", "")
#             )

#             st.session_state.last_analysis = {
#                 "text": text,
#                 "dialect": dialect,
#                 "sentiment": sentiment
#             }

#             save_analysis(
#                 st.session_state.user["id"],
#                 text,
#                 dialect["dialect"],
#                 sentiment["sentiment"],
#                 sentiment["confidence"],
#                 explanation
#             )

#         except Exception as e:
#             st.error(f"Analysis error: {e}")

#     result = st.session_state.last_analysis

#     if result:

#         d = result["dialect"]
#         s = result["sentiment"]

#         st.divider()

#         c1, c2, c3 = st.columns(3)

#         c1.metric("Dialect", d["dialect"])
#         c2.metric("Sentiment", s["sentiment"])

#         c3.metric(
#             "Confidence",
#             f'{s["confidence"] * 100:.1f}%'
#         )

#         st.subheader("Dialect Explanation")
#         st.write(d["explanation"])

#         st.write("**Linguistic clues:**")
#         st.write(", ".join(d.get("linguistic_clues", [])))

#         st.subheader("Sentiment Explanation")
#         st.write(s["explanation"])

#         st.write("**Emotional words:**")
#         st.write(", ".join(s.get("emotional_words", [])))

#         st.subheader("Sentiment Score")

#         scores = pd.DataFrame({
#             "Sentiment": [
#                 "Positive",
#                 "Negative",
#                 "Neutral"
#             ],
#             "Score": [
#                 s["positive_score"],
#                 s["negative_score"],
#                 s["neutral_score"]
#             ]
#         })

#         fig = px.bar(
#             scores,
#             x="Sentiment",
#             y="Score",
#             text="Score",
#             range_y=[0, 100]
#         )

#         st.plotly_chart(
#             fig,
#             use_container_width=True
#         )

#         st.info(s.get("suggestion", ""))

#         st.caption(
#             "Model estimates are not clinical assessments "
#             "or verified dialect classifications."
#         )


# # MOOD CHAT
# elif st.session_state.page == "Mood Chat":

#     st.header("💚 Mood Companion")

#     st.write("তোমার মনের কথা এখানে নির্দ্বিধায় বলতে পারো।")

#     st.caption(
#         "Your conversation is kept only in this active session."
#     )

#     if st.button("Clear conversation"):
#         st.session_state.chat_history = []
#         st.rerun()

#     if not st.session_state.chat_history:

#         with st.chat_message("assistant"):
#             st.write(
#                 "হ্যালো! 🌿 কেমন আছো আজকে? "
#                 "মন খুলে বলতে পারো। আমি শুনছি।"
#             )

#     for message in st.session_state.chat_history:

#         with st.chat_message(message["role"]):
#             st.markdown(message["content"])

#     prompt = st.chat_input("তোমার মনের কথা লিখো...")

#     if prompt:

#         with st.chat_message("user"):
#             st.markdown(prompt)

#         with st.chat_message("assistant"):

#             with st.spinner("তোমার কথা শুনছি..."):

#                 try:
#                     answer = get_chat_response(
#                         st.session_state.chat_history,
#                         prompt
#                     )

#                 except Exception as e:
#                     answer = (
#                         "দুঃখিত, এই মুহূর্তে উত্তর তৈরি "
#                         "করতে সমস্যা হচ্ছে। একটু পরে চেষ্টা করো।"
#                     )
#                     st.error(str(e))

#                 st.markdown(answer)

#         st.session_state.chat_history.extend([
#             {
#                 "role": "user",
#                 "content": prompt
#             },
#             {
#                 "role": "assistant",
#                 "content": answer
#             }
#         ])

#     st.divider()

#     st.subheader("🌱 Take a small break")

#     st.write("""
#     - ধীরে শ্বাস নাও।
#     - কিছুক্ষণ বিশ্রাম নাও।
#     - নিজের অনুভূতি লিখে রাখো।
#     - প্রয়োজন হলে বিশ্বস্ত কারও সঙ্গে কথা বলো।
#     """)


# # JOURNAL
# elif st.session_state.page == "My Journal":

#     st.header("📖 My Journal")

#     history = get_history(
#         st.session_state.user["id"]
#     )

#     if not history:

#         st.info(
#             "No analysis history yet. "
#             "Start with Dialect Lab."
#         )

#     else:

#         df = pd.DataFrame(history)

#         st.metric("Total Analyses", len(df))

#         st.subheader("Sentiment Distribution")

#         counts = (
#             df["sentiment"]
#             .value_counts()
#             .reset_index()
#         )

#         counts.columns = ["Sentiment", "Count"]

#         fig = px.pie(
#             counts,
#             names="Sentiment",
#             values="Count",
#             hole=0.45
#         )

#         st.plotly_chart(
#             fig,
#             use_container_width=True
#         )

#         st.subheader("Analysis History")

#         st.dataframe(
#             df,
#             use_container_width=True,
#             hide_index=True
#         )


# # SIGN OUT
# st.divider()

# if st.button("Sign Out"):

#     st.session_state.user = None
#     st.session_state.chat_history = []
#     st.session_state.last_analysis = None
#     st.session_state.page = "Home"

#     st.rerun()


# st.caption(
#     "DialectMood AI | Bangla Dialect Intelligence Platform"
# )


import streamlit as st
import pandas as pd
import plotly.express as px

from database import init_db, save_analysis, get_history
from auth import auth_page
from dialect_service import identify_dialect
from sentiment_service import analyze_sentiment
from chatbot_service import get_chat_response
from chart_memory import (
    init_chat_db,
    save_messages,
    load_messages,
    clear_messages
)


# PAGE CONFIGURATION
st.set_page_config(
    page_title="DialectMood AI",
    page_icon="🌿",
    layout="wide"
)


# CUSTOM CSS
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Hind+Siliguri:wght@400;500;600;700;800&display=swap');

html, body, [class*="css"] {
    font-family: 'Hind Siliguri', sans-serif;
}

.stApp {
    background-color: #F5FAF6;
}

.main-title {
    color: #267653;
    font-size: 30px;
    font-weight: 800;
    margin-bottom: 5px;
}

.hero {
    background: linear-gradient(120deg, #174B36 0%, #4B9873 100%);
    padding: 45px;
    border-radius: 20px;
    color: #FFFFFF;
    width: 100%;
    box-sizing: border-box;
    margin: 15px 0 25px 0;
    box-shadow: 0 8px 25px rgba(23, 75, 54, 0.15);
}

.hero h1 {
    color: #FFFFFF !important;
    font-size: clamp(26px, 4vw, 42px);
    font-weight: 800;
    line-height: 1.3;
    margin: 0 0 8px 0;
    padding: 0;
}

.hero p {
    color: #E7F5EC !important;
    font-size: 17px;
    line-height: 1.8;
    margin: 18px 0 0 0;
    max-width: 650px;
}

@media screen and (max-width: 768px) {
    .hero {
        padding: 25px 20px;
        border-radius: 15px;
    }

    .hero p {
        font-size: 15px;
    }

    .main-title {
        font-size: 25px;
    }
}
</style>
""", unsafe_allow_html=True)


# HELPERS
def build_mood_context(user_id, limit=5):
    """
    Dialect Lab-er recent analysis theke chatbot-er jonno short context toiri kore.
    get_history()-er row gulo dict hishebe dhora hoyeche.
    """
    lines = []

    try:
        history = list(get_history(user_id))

        # newest first korar chesta (jodi date/id column thake)
        for key in ("created_at", "timestamp", "date", "id"):
            if history and isinstance(history[0], dict) and key in history[0]:
                history.sort(key=lambda r: r.get(key) or "", reverse=True)
                break

        for row in history[:limit]:
            if not isinstance(row, dict):
                continue

            snippet = str(row.get("text", ""))[:80]

            lines.append(
                f'- sentiment: {row.get("sentiment", "?")}, '
                f'dialect: {row.get("dialect", "?")}, '
                f'text: "{snippet}"'
            )
    except Exception:
        pass

    # ei session-er last analysis
    last = st.session_state.get("last_analysis")

    if last:
        try:
            lines.insert(
                0,
                f'- (latest) sentiment: {last["sentiment"]["sentiment"]}, '
                f'dialect: {last["dialect"]["dialect"]}, '
                f'text: "{last["text"][:80]}"'
            )
        except Exception:
            pass

    return "\n".join(lines)


# INITIALIZATION
init_db()
init_chat_db()

if "user" not in st.session_state:
    st.session_state.user = None

if "page" not in st.session_state:
    st.session_state.page = "Home"

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "visible_chat_history" not in st.session_state:
    st.session_state.visible_chat_history = []
if "chat_loaded_for" not in st.session_state:
    st.session_state.chat_loaded_for = None

if "last_analysis" not in st.session_state:
    st.session_state.last_analysis = None


# AUTHENTICATION
if st.session_state.user is None:
    auth_page()
    st.stop()


# LOAD SAVED CHAT MEMORY (login-er por ekbar)
if st.session_state.chat_loaded_for != st.session_state.user["id"]:
    st.session_state.chat_history = load_messages(
        st.session_state.user["id"]
    )
    st.session_state.chat_loaded_for = st.session_state.user["id"]


# NAVBAR
st.markdown(
    '<div class="main-title">🌿 DialectMood AI</div>',
    unsafe_allow_html=True
)

st.caption("Your Bangla Dialect Intelligence & Mood Companion")

pages = ["Home", "Dialect Lab", "Mood Chat", "My Journal"]

columns = st.columns(4)

for col, page in zip(columns, pages):
    with col:
        if st.button(
            page,
            use_container_width=True,
            type="primary" if st.session_state.page == page else "secondary"
        ):
            st.session_state.page = page
            st.rerun()

st.divider()

st.write(f"Welcome back, **{st.session_state.user['name']}** 🌿")


# HOME
if st.session_state.page == "Home":

    st.markdown("""
    <div class="hero">
        <h1>Understand Your Dialect.</h1>
        <h1>Understand Your Emotions.</h1>
        <p>
            Explore Dinajpur and Rangpur dialects,
            discover emotional expressions and talk
            with your AI mood companion.
        </p>
    </div>
    """, unsafe_allow_html=True)

    st.write("")

    c1, c2, c3 = st.columns(3)

    c1.metric("Regional Dialects", "2+")
    c2.metric("Sentiment Classes", "4")
    c3.metric("AI Companion", "Active")

    st.subheader("Explore your AI platform")

    a, b = st.columns(2)

    with a:
        if st.button("🧭 Explore Dialect Lab", use_container_width=True):
            st.session_state.page = "Dialect Lab"
            st.rerun()

    with b:
        if st.button("💚 Talk to Mood Companion", use_container_width=True):
            st.session_state.page = "Mood Chat"
            st.rerun()


# DIALECT LAB
elif st.session_state.page == "Dialect Lab":

    st.header("🧭 Dialect & Sentiment Analysis")

    st.write(
        "Write a Bangla sentence to analyze its dialect and emotion."
    )

    text = st.text_area(
        "Enter your text",
        height=150,
        placeholder="মুই আজকে খুব ভালো আছি..."
    )

    if st.button(
        "Analyze Text",
        type="primary",
        disabled=not text.strip()
    ):

        try:
            with st.spinner("Analyzing dialect and sentiment..."):

                dialect = identify_dialect(text)
                sentiment = analyze_sentiment(text)

            explanation = (
                dialect.get("explanation", "")
                + " "
                + sentiment.get("explanation", "")
            )

            st.session_state.last_analysis = {
                "text": text,
                "dialect": dialect,
                "sentiment": sentiment
            }

            save_analysis(
                st.session_state.user["id"],
                text,
                dialect["dialect"],
                sentiment["sentiment"],
                sentiment["confidence"],
                explanation
            )

        except Exception as e:
            st.error(f"Analysis error: {e}")

    result = st.session_state.last_analysis

    if result:

        d = result["dialect"]
        s = result["sentiment"]

        st.divider()

        c1, c2, c3 = st.columns(3)

        c1.metric("Dialect", d["dialect"])
        c2.metric("Sentiment", s["sentiment"])

        c3.metric(
            "Confidence",
            f'{s["confidence"] * 100:.1f}%'
        )

        st.subheader("Dialect Explanation")
        st.write(d["explanation"])

        st.write("**Linguistic clues:**")
        st.write(", ".join(d.get("linguistic_clues", [])))

        st.subheader("Sentiment Explanation")
        st.write(s["explanation"])

        st.write("**Emotional words:**")
        st.write(", ".join(s.get("emotional_words", [])))

        st.subheader("Sentiment Score")

        scores = pd.DataFrame({
            "Sentiment": [
                "Positive",
                "Negative",
                "Neutral"
            ],
            "Score": [
                s["positive_score"],
                s["negative_score"],
                s["neutral_score"]
            ]
        })

        fig = px.bar(
            scores,
            x="Sentiment",
            y="Score",
            text="Score",
            range_y=[0, 100]
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

        st.info(s.get("suggestion", ""))

        st.caption(
            "Model estimates are not clinical assessments "
            "or verified dialect classifications."
        )


# MOOD CHAT
elif st.session_state.page == "Mood Chat":

    st.header("💚 Mood Companion")

    st.write("তোমার মনের কথা এখানে নির্দ্বিধায় বলতে পারো।")

    st.caption(
        "তোমার কথোপকথন তোমার অ্যাকাউন্টে সংরক্ষিত থাকে, "
        "যাতে আমি আগের কথা মনে রাখতে পারি। "
        "চাইলে নিচের বাটন দিয়ে মুছে ফেলতে পারো।"
    )

    if st.button("Clear conversation"):
        clear_messages(st.session_state.user["id"])
        st.session_state.chat_history = []
        st.rerun()

    if not st.session_state.chat_history:

        with st.chat_message("assistant"):
            st.write(
                "হ্যালো! 🌿 কেমন আছো আজকে? "
                "মন খুলে বলতে পারো। আমি শুনছি।"
            )

    for message in st.session_state.chat_history:

        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    prompt = st.chat_input("তোমার মনের কথা লিখো...")

    if prompt:

        with st.chat_message("user"):
            st.markdown(prompt)

        answer = None

        with st.chat_message("assistant"):

            with st.spinner("তোমার কথা শুনছি..."):

                try:
                    answer = get_chat_response(
                        st.session_state.chat_history,
                        prompt,
                        user_name=st.session_state.user["name"],
                        mood_context=build_mood_context(
                            st.session_state.user["id"]
                        )
                    )

                    st.markdown(answer)

                except Exception as e:
                    st.markdown(
                        "দুঃখিত, এই মুহূর্তে উত্তর তৈরি "
                        "করতে সমস্যা হচ্ছে। একটু পরে চেষ্টা করো।"
                    )
                    st.error(str(e))

        # shudhu successful reply hole history-te save hobe
        if answer:

            new_messages = [
                {
                    "role": "user",
                    "content": prompt
                },
                {
                    "role": "assistant",
                    "content": answer
                }
            ]

            st.session_state.chat_history.extend(new_messages)

            save_messages(
                st.session_state.user["id"],
                new_messages
            )

    st.divider()



# JOURNAL
elif st.session_state.page == "My Journal":

    st.header("📖 My Journal")

    history = get_history(
        st.session_state.user["id"]
    )

    if not history:

        st.info(
            "No analysis history yet. "
            "Start with Dialect Lab."
        )

    else:

        df = pd.DataFrame(history)

        st.metric("Total Analyses", len(df))

        st.subheader("Sentiment Distribution")

        counts = (
            df["sentiment"]
            .value_counts()
            .reset_index()
        )

        counts.columns = ["Sentiment", "Count"]

        fig = px.pie(
            counts,
            names="Sentiment",
            values="Count",
            hole=0.45
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

        st.subheader("Analysis History")

        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True
        )


# SIGN OUT
    st.divider()

    # SIGN OUT BUTTON - MOOD CHAT PAGE
    st.subheader("Account")

    logout_col1, logout_col2, logout_col3 = st.columns([1, 2, 1])

    with logout_col2:

        if st.button(
            "🚪 Sign Out",
            use_container_width=True,
            type="primary"
        ):

            st.session_state.user = None
            st.session_state.chat_history = []
            st.session_state.visible_chat_history = []
            st.session_state.chat_loaded_for = None
            st.session_state.last_analysis = None
            st.session_state.page = "Home"

            st.rerun()

# st.caption(
#     "DialectMood AI | Bangla Dialect Intelligence Platform"
# )