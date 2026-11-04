import os

import streamlit as st

from dotenv import load_dotenv
from langchain_groq import ChatGroq


load_dotenv()


def get_api_key():

    try:
        key = st.secrets.get("GROQ_API_KEY")
        if key:
            return key
    except Exception:
        pass

    return os.getenv("GROQ_API_KEY")


def get_model_name():

    try:
        model = st.secrets.get("GROQ_MODEL")
        if model:
            return model
    except Exception:
        pass

    return os.getenv(
        "GROQ_MODEL",
        "openai/gpt-oss-120b"
    )


def get_llm(temperature=0.3):

    api_key = get_api_key()

    if not api_key:

        raise ValueError(
            "GROQ_API_KEY missing. "
            "Configure .env or Streamlit Secrets."
        )

    return ChatGroq(
        model=get_model_name(),
        api_key=api_key,
        temperature=temperature
    )