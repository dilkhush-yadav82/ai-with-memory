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

# Configure Gemini API
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

MODEL_NAME = "gemini-1.5-flash"
HISTORY_FILE = "conversation_history.json"
MAX_HISTORY = 20

# ---------------- MEMORY FUNCTIONS ----------------

def load_history():
    if Path(HISTORY_FILE).exists():
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []

def save_history(history):
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2, ensure_ascii=False)

def clear_history():
    save_history([])

# ---------------- CHAT LOGIC ----------------

def build_prompt(history):
    prompt = ""
    for msg in history[-MAX_HISTORY:]:
        prompt += f"{msg['role'].upper()}: {msg['content']}\n"
    return prompt

def chat_with_memory(user_message, history):
    # Add system message once
    if not history:
        history.append({
            "role": "system",
            "content": (
                "You are a helpful AI assistant with memory. "
                "You remember previous user details and can reference them later."
            )
        })

    # Add user message
    history.append({
        "role": "user",
        "content": user_message
    })

    prompt = build_prompt(history)

    model = genai.GenerativeModel(MODEL_NAME)
    response = model.generate_content(prompt)

    assistant_message = response.text.strip()

    # Add assistant response
    history.append({
        "role": "assistant",
        "content": assistant_message
    })

    save_history(history)
    return assistant_message

# ---------------- STREAMLIT UI ----------------

st.title("🧠 AI with Memory")
st.caption("A conversational AI that remembers you across sessions")

history = load_history()

# Display previous conversation
for msg in history:
    if msg["role"] == "user":
        st.markdown(f"**You:** {msg['content']}")
    elif msg["role"] == "assistant":
        st.markdown(f"**AI:** {msg['content']}")

st.divider()

user_input = st.text_input("Type your message")

col1, col2 = st.columns([1, 1])

with col1:
    send_clicked = st.button("Send")

with col2:
    clear_clicked = st.button("Clear Memory")

if send_clicked and user_input.strip():
    with st.spinner("Thinking..."):
        reply = chat_with_memory(user_input, history)
    st.experimental_rerun()

if clear_clicked:
    clear_history()
    st.success("Memory cleared!")
    st.experimental_rerun()

st.divider()
st.markdown(
    """
**How this works**
- Conversation memory is stored locally in JSON
- Previous messages are sent back to the model for context
- Memory persists across sessions
- Built using Streamlit + Gemini API
"""
)
