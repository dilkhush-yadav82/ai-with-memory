import streamlit as st
import json
from pathlib import Path
from google import genai

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

# ---------------- SESSION STATE (UI ONLY) ----------------

if "chat" not in st.session_state:
    st.session_state.chat = []

# ---------------- PROMPT BUILDER ----------------

def build_prompt(memory, session_chat):
    combined = memory + session_chat
    return "\n".join(
        f"{m['role'].upper()}: {m['content']}"
        for m in combined[-MAX_HISTORY:]
    )

# ---------------- CHAT LOGIC ----------------

def chat_with_memory(user_message):
    memory = load_memory()

    # System message (only once)
    if not memory:
        memory.append({
            "role": "system",
            "content": (
                "You are a helpful AI assistant with memory. "
                "You remember user details across sessions but do not repeat old chats unless needed."
            )
        })

    # Add to UI session
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
        assistant_message = "⚠️ Sorry, I couldn't respond right now. Please try again."
        st.error(f"Gemini error: {e}")

    # Add assistant reply to UI
    st.session_state.chat.append({
        "role": "assistant",
        "content": assistant_message
    })

    # Save to long-term memory only if successful
    if "couldn't respond" not in assistant_message:
        memory.append({"role": "user", "content": user_message})
        memory.append({"role": "assistant", "content": assistant_message})
        save_memory(memory)

# ---------------- DISPLAY CHAT ----------------

for msg in st.session_state.chat:
    if msg["role"] == "user":
        st.markdown(f"**You:** {msg['content']}")
    else:
        st.markdown(f"**AI:** {msg['content']}")

st.divider()

# ---------------- INPUT FORM (ENTER KEY WORKS) ----------------

with st.form("chat_form", clear_on_submit=True):
    user_message = st.text_input("Type your message")
    send_clicked = st.form_submit_button("Send")

col1, col2 = st.columns(2)

with col1:
    clear_chat_clicked = st.button("Clear Chat")

with col2:
    clear_memory_clicked = st.button("Clear Memory")

# ---------------- ACTIONS ----------------

if send_clicked and user_message.strip():
    with st.spinner("Thinking..."):
        chat_with_memory(user_message)
    st.rerun()

if clear_chat_clicked:
    st.session_state.chat = []
    st.success("Session closed (chat cleared)")
    st.rerun()

if clear_memory_clicked:
    clear_memory()
    st.session_state.chat = []
    st.success("Memory wiped (new user)")
    st.rerun()

st.divider()

st.markdown(
    """
**How this works**
- Enter key or Send button submits message
- UI chat resets every session
- Memory persists across sessions
- Clear Chat = new session
- Clear Memory = forget user
"""
)
