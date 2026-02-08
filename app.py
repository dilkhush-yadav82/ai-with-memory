import streamlit as st
import json
from pathlib import Path
import google.generativeai as genai
import os

# ---------------- CONFIG ----------------

st.set_page_config(
    page_title="AI with Memory",
    page_icon="🧠",
    layout="centered"
)

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

MODEL_NAME = "gemini-1.5-flash"
HISTORY_FILE = "conversation_history.json"
MAX_HISTORY = 20

# ---------------- MEMORY (LONG-TERM) ----------------

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
    st.session_state.chat = []   # UI messages only

# ---------------- CHAT LOGIC ----------------

def build_prompt(memory, session_chat):
    combined = memory + session_chat
    prompt = ""
    for msg in combined[-MAX_HISTORY:]:
        prompt += f"{msg['role'].upper()}: {msg['content']}\n"
    return prompt

def chat_with_memory(user_message):
    memory = load_memory()

    if not memory:
        memory.append({
            "role": "system",
            "content": (
                "You are a helpful AI assistant with memory. "
                "You remember user details across sessions but do not repeat old chats unless needed."
            )
        })

    # Session chat (UI only)
    st.session_state.chat.append({
        "role": "user",
        "content": user_message
    })

    prompt = build_prompt(memory, st.session_state.chat)

    model = genai.GenerativeModel(MODEL_NAME)
    response = model.generate_content(prompt)
    assistant_message = response.text.strip()

    # Save to session chat
    st.session_state.chat.append({
        "role": "assistant",
        "content": assistant_message
    })

    # Save to long-term memory
    memory.append({"role": "user", "content": user_message})
    memory.append({"role": "assistant", "content": assistant_message})
    save_memory(memory)

# ---------------- UI ----------------

st.title("🧠 AI with Memory")
st.caption("Remembers you across sessions, not chats")

# Display SESSION chat only
for msg in st.session_state.chat:
    if msg["role"] == "user":
        st.markdown(f"**You:** {msg['content']}")
    else:
        st.markdown(f"**AI:** {msg['content']}")

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
**How it works**
- Chat UI resets every session
- Memory persists across sessions
- Memory is used only for reasoning
- Built with Streamlit + Gemini
"""
)
