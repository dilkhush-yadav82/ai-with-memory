import streamlit as st
import json
from pathlib import Path
from google import genai
from google.genai import types
import pandas as pd

# ================= PAGE CONFIG =================

st.set_page_config(
    page_title="AI with Memory",
    page_icon="🧠",
    layout="centered"
)

st.title("🧠 AI with Memory")
st.caption("Remembers you across sessions, not chats")

# ================= GEMINI CONFIG =================

client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])

MODEL_NAME = "models/gemini-flash-latest"

# ================= STORAGE CONFIG =================

HISTORY_FILE = "conversation_history.json"
MAX_CONTEXT_MESSAGES = 20     # sent to model
MAX_STORED_MESSAGES = 2000    # stored on disk

# ================= MEMORY =================

def load_memory():
    if Path(HISTORY_FILE).exists():
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []

def save_memory(memory):
    memory = memory[-MAX_STORED_MESSAGES:]
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(memory, f, indent=2, ensure_ascii=False)

def clear_memory():
    save_memory([])

# ================= SESSION STATE =================

if "chat" not in st.session_state:
    st.session_state.chat = []

# ================= PROMPT BUILDER =================

def build_prompt(memory, session_chat):
    combined = memory + session_chat
    recent = combined[-MAX_CONTEXT_MESSAGES:]
    return "\n".join(
        f"{m['role'].upper()}: {m['content']}" for m in recent
    )

# ================= FILE PROCESSING =================

def extract_file_content(uploaded_file):
    if uploaded_file.type == "text/plain":
        return uploaded_file.read().decode("utf-8")

    if uploaded_file.type == "text/csv":
        df = pd.read_csv(uploaded_file)
        return df.head(50).to_string()

    if uploaded_file.type == "application/pdf":
        return "PDF uploaded. Summarize or extract key points."

    return "Unsupported file type."

# ================= CHAT LOGIC =================

def chat_with_memory(user_message, image=None, file_text=None):
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

    contents = [prompt]

    if file_text:
        contents.append(f"\nUser uploaded file content:\n{file_text}")

    if image:
        contents.append(
            types.Part.from_bytes(
                data=image.read(),
                mime_type=image.type
            )
        )

    try:
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=contents
        )
        assistant_message = response.text.strip()
    except Exception as e:
        assistant_message = "⚠️ Error generating response."
        st.error(str(e))

    st.session_state.chat.append({
        "role": "assistant",
        "content": assistant_message
    })

    if "Error generating response" not in assistant_message:
        memory.append({"role": "user", "content": user_message})
        memory.append({"role": "assistant", "content": assistant_message})
        save_memory(memory)

# ================= UI DISPLAY =================

for msg in st.session_state.chat:
    st.markdown(
        f"**{'You' if msg['role']=='user' else 'AI'}:** {msg['content']}"
    )

st.divider()

# ================= INPUT FORM =================

with st.form("chat_form", clear_on_submit=True):
    user_message = st.text_input("Type your message")
    uploaded_image = st.file_uploader(
        "Upload image (optional)",
        type=["jpg", "png", "jpeg"]
    )
    uploaded_file = st.file_uploader(
        "Upload file (txt, csv, pdf)",
        type=["txt", "csv", "pdf"]
    )

    send_clicked = st.form_submit_button("Send")

# ================= BUTTONS =================

col1, col2 = st.columns(2)

with col1:
    clear_chat_clicked = st.button("Clear Chat")

with col2:
    clear_memory_clicked = st.button("Clear Memory")

# ================= ACTIONS =================

if send_clicked and user_message.strip():
    file_text = extract_file_content(uploaded_file) if uploaded_file else None

    with st.spinner("Thinking..."):
        chat_with_memory(
            user_message,
            image=uploaded_image,
            file_text=file_text
        )
    st.rerun()

if clear_chat_clicked:
    st.session_state.chat = []
    st.success("Session closed")
    st.rerun()

if clear_memory_clicked:
    clear_memory()
    st.session_state.chat = []
    st.success("Memory wiped")
    st.rerun()

# ================= MEMORY VIEWER =================

with st.expander("📚 View Stored Memory"):
    memory = load_memory()
    st.json(memory)

    st.download_button(
        label="Download Memory",
        data=json.dumps(memory, indent=2),
        file_name="memory.json",
        mime="application/json"
    )

st.divider()

st.markdown(
    """
**Capabilities**
- Enter key submits message
- Image + file understanding
- Session UI resets independently
- Long-term memory stored on disk
- Scales safely beyond context limits
"""
)
