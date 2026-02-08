import streamlit as st
import json
import re
from pathlib import Path
from google import genai

# ================= PAGE =================

st.set_page_config(
    page_title="AI with Memory",
    page_icon="🧠",
    layout="centered"
)

st.title("🧠 AI with Memory")
st.caption("Remembers you across sessions")

# ================= GEMINI =================

client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
MODEL = "models/gemini-flash-latest"

# ================= STORAGE =================

MEMORY_FILE = "memory.json"
MAX_CONTEXT = 15

def load_memory():
    if Path(MEMORY_FILE).exists():
        return json.load(open(MEMORY_FILE, "r", encoding="utf-8"))
    return []

def save_memory(mem):
    json.dump(mem, open(MEMORY_FILE, "w", encoding="utf-8"), indent=2)

def clean_for_voice(text):
    text = re.sub(r"[#*_>`]", "", text)
    return text.strip()

# ================= SESSION =================

if "chat" not in st.session_state:
    st.session_state.chat = []

# ================= CHAT DISPLAY =================

for i, msg in enumerate(st.session_state.chat):
    if msg["role"] == "user":
        st.markdown(f"**You:** {msg['content']}")
    else:
        col1, col2 = st.columns([10, 1])
        with col1:
            st.markdown(f"**AI:** {msg['content']}")
        with col2:
            if st.button("🔊", key=f"speak_{i}"):
                speak_text = clean_for_voice(msg["content"])
                st.components.v1.html(
                    f"""
                    <script>
                    const msg = new SpeechSynthesisUtterance({json.dumps(speak_text)});
                    msg.lang = "en-US";
                    window.speechSynthesis.cancel();
                    window.speechSynthesis.speak(msg);
                    </script>
                    """,
                    height=0
                )

st.divider()

# ================= INPUT =================

with st.form("chat_form", clear_on_submit=True):
    user_input = st.text_input("Type your message")
    send = st.form_submit_button("Send")

# ================= CHAT LOGIC =================

if send and user_input.strip():
    memory = load_memory()

    if not memory:
        memory.append({
            "role": "system",
            "content": "You are a friendly personal assistant who remembers user details."
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

# ================= FOOTER =================

st.divider()
st.caption(
    "🔹 This assistant focuses on memory, transparency, and calm UX — not gimmicks."
)
