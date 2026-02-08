import streamlit as st
import json
from pathlib import Path
from google import genai
import os

# ---------------- PAGE CONFIG ----------------

st.set_page_config(
    page_title="AI with Memory",
    page_icon="🧠",
    layout="centered"
)

st.title("🧠 AI with Memory")
st.caption("Remembers you across sessions, not chats")

# ---------------- GEMINI CONFIG ----------------

client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])

MODEL_NAME = "models/gemini-flash-latest"
HISTORY_FILE = "conversation_history.json"
MAX_HISTORY = 20

# ---------------- LONG-TERM MEMORY ----------------

def load_memory():
    if Path(HISTORY_FILE).exists():
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []

def save_memory(memory):
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(memory, f, indent=2, ensure_ascii=False)

def clear_memory():
    save_memory([])

# ---------------- SESSION STATE ----------------

if "chat" not in st.session_state:
    st.session_state.chat = []

# ---------------- PROMPT BUILDER ----------------

def build_prompt(memory, session_chat):
    combined = memory + session_chat
    return "\n".join(
        f"{m['role'].upper()}: {m['content']}"
        for m in combined[-MAX_HISTORY:]
    )

# ---------------- CHAT FUNCTION ----------------

def chat_with_memory(user_message):
    memory = load_memory()

    if not memory:
        memory.append({
            "role": "system",
            "content": (
                "You are a helpful AI assistant with memory. "
                "You remember user details across sessions but do not repeat old chats."
            )
        })

    st.session_state.chat.append({
        "role": "user",
        "content": user_message
    })

    prompt = build_prompt(memory, st.session_state.chat)

    try:
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=prompt
        )
        assistant_message = response.text.strip()

    except Exception as e:
        assistant_message = (
            "⚠️ Sorry, I'm temporarily unable to respond. Please try again."
        )
        st.error(f"Gemini API error: {e}")

    st.session_state.chat.append({
        "role": "assistant",
        "content": assistant_message
    })

    if "temporarily unable" not in assistant_message:
        memory.append({"role": "user", "content": user_message})
        memory.append({"role": "assistant", "content": assistant_message})
        save_memory(memory)

# ---------------- UI ----------------

for msg in st.session_state.chat:
    st.markdown(
        f"**{'You' if msg['role']=='user' else 'AI'}:** {msg['content']}"
    )

st.divider()

user_input = st.text_input("Type your message")

col1, col2, col3 = st.columns(3)

with col1:
    send_clicked = st.button("Send")

with col2:
    clear_chat_clicked = st.button("Clear Chat")

with col3:
    clear_memory_clicked = st.button("Clear Memory")

if send_clicked and user_input.strip():
    with st.spinner("Thinking..."):
        chat_with_memory(user_input)
    st.rerun()

if clear_chat_clicked:
    st.session_state.chat = []
    st.success("Session chat cleared")
    st.rerun()

if clear_memory_clicked:
    clear_memory()
    st.session_state.chat = []
    st.success("Memory cleared")
    st.rerun()

st.divider()
st.markdown(
    """
**How this works**
- UI chat resets every session
- Memory persists across sessions
- Uses Gemini 1.5 Flash
- Built with Streamlit
"""
)
