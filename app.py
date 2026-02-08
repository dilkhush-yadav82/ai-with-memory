import streamlit as st
import json
from pathlib import Path
from google import genai

# ================== CONFIG ==================

st.set_page_config(
    page_title="AI with Memory",
    page_icon="🧠",
    layout="centered"
)

client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
MODEL = "models/gemini-flash-latest"

MEMORY_FILE = "memory.json"
MAX_CONTEXT = 15

# ================== MEMORY ==================

def load_memory():
    if Path(MEMORY_FILE).exists():
        return json.load(open(MEMORY_FILE, "r", encoding="utf-8"))
    return []

def save_memory(memory):
    json.dump(memory, open(MEMORY_FILE, "w", encoding="utf-8"), indent=2)

def clear_memory():
    save_memory([])

# ================== SESSION ==================

if "chat" not in st.session_state:
    st.session_state.chat = []

if "language" not in st.session_state:
    st.session_state.language = "English"

# ================== HEADER ==================

st.markdown(
    """
    <h2 style="text-align:center;">🧠 AI with Memory</h2>
    <p style="text-align:center;color:gray;">
    A calm assistant that remembers you across sessions
    </p>
    """,
    unsafe_allow_html=True
)

# ================== LANGUAGE SELECTOR ==================

st.markdown(
    "<p style='text-align:center;color:#666;'>Response language</p>",
    unsafe_allow_html=True
)

st.session_state.language = st.radio(
    "",
    ["English", "Hindi", "Hinglish"],
    horizontal=True
)

st.divider()

# ================== CHAT DISPLAY ==================

def chat_bubble(role, text):
    if role == "user":
        st.markdown(
            f"""
            <div style="
                background:#DCF8C6;
                padding:12px;
                border-radius:10px;
                margin-bottom:8px;
                max-width:80%;
                margin-left:auto;
            ">
            {text}
            </div>
            """,
            unsafe_allow_html=True
        )
    else:
        st.markdown(
            f"""
            <div style="
                background:#F1F0F0;
                padding:12px;
                border-radius:10px;
                margin-bottom:12px;
                max-width:80%;
            ">
            {text}
            </div>
            """,
            unsafe_allow_html=True
        )

for msg in st.session_state.chat:
    chat_bubble(msg["role"], msg["content"])

# ================== INPUT ==================

with st.form("chat_form", clear_on_submit=True):
    user_input = st.text_input("Type your message here…")
    send = st.form_submit_button("Send")

# ================== CHAT LOGIC ==================

if send and user_input.strip():
    memory = load_memory()

    # Language instruction
    if st.session_state.language == "Hindi":
        lang_instruction = "Respond only in Hindi."
    elif st.session_state.language == "Hinglish":
        lang_instruction = "Respond in Hinglish (mix of Hindi and English)."
    else:
        lang_instruction = "Respond in English."

    if not memory:
        memory.append({
            "role": "system",
            "content": (
                "You are a friendly personal assistant. "
                "You remember user details across sessions. "
                f"{lang_instruction} "
                "Keep responses natural and concise."
            )
        })

    st.session_state.chat.append({
        "role": "user",
        "content": user_input
    })

    combined = memory + st.session_state.chat

    prompt = "\n".join(
        f"{m['role'].upper()}: {m['content']}"
        for m in combined[-MAX_CONTEXT:]
    )

    response = client.models.generate_content(
        model=MODEL,
        contents=prompt
    )

    reply = response.text.strip()

    st.session_state.chat.append({
        "role": "assistant",
        "content": reply
    })

    memory.append({"role": "user", "content": user_input})
    memory.append({"role": "assistant", "content": reply})
    save_memory(memory)

    st.rerun()

# ================== FOOTER ACTIONS ==================

st.divider()

col1, col2 = st.columns(2)

with col1:
    if st.button("🆕 New Chat"):
        st.session_state.chat = []
        st.rerun()

with col2:
    if st.button("🧠 Clear Memory"):
        clear_memory()
        st.session_state.chat = []
        st.success("Memory cleared")

# ================== MEMORY VIEW ==================

with st.expander("🧠 What I remember about you"):
    memory = load_memory()
    if len(memory) <= 1:
        st.info("I haven’t learned anything personal yet.")
    else:
        for m in memory:
            if m["role"] != "system":
                st.markdown(f"- {m['content']}")

# ================== FOOTER ==================

st.markdown(
    """
    <hr>
    <p style="text-align:center;color:gray;font-size:13px;">
    Built for clarity, trust, and long-term memory — not gimmicks.
    </p>
    """,
    unsafe_allow_html=True
)
