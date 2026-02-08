import streamlit as st
import json
from pathlib import Path
from google import genai
import PyPDF2

# ================= PAGE CONFIG =================

st.set_page_config(
    page_title="AI Assistant with Memory",
    page_icon="🧠",
    layout="wide"
)

st.title("🧠 AI Assistant with Memory")
st.caption("Memory • Multimodal • Hindi • ChatGPT-like uploads")

# ================= GEMINI CONFIG =================

client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
MODEL = "models/gemini-flash-latest"

# ================= STORAGE =================

MEMORY_FILE = "conversation_history.json"
MAX_CONTEXT = 20

# ================= MEMORY =================

def load_memory():
    if Path(MEMORY_FILE).exists():
        return json.load(open(MEMORY_FILE, "r", encoding="utf-8"))
    return []

def save_memory(mem):
    json.dump(mem, open(MEMORY_FILE, "w", encoding="utf-8"), indent=2, ensure_ascii=False)

def clear_memory():
    save_memory([])

# ================= SESSION STATE =================

if "chat" not in st.session_state:
    st.session_state.chat = []

if "language" not in st.session_state:
    st.session_state.language = "English"

if "voice" not in st.session_state:
    st.session_state.voice = True

if "speak_now" not in st.session_state:
    st.session_state.speak_now = False

# ================= SIDEBAR =================

st.sidebar.subheader("🌐 Language")
st.session_state.language = st.sidebar.radio(
    "Response language",
    ["English", "Hindi"]
)

st.sidebar.subheader("🔊 Voice Output")
st.session_state.voice = st.sidebar.checkbox("Speak responses", value=True)

if not st.session_state.voice:
    st.components.v1.html(
        "<script>window.speechSynthesis.cancel();</script>",
        height=0
    )

st.sidebar.divider()

if st.sidebar.button("🧠 Clear Memory"):
    clear_memory()
    st.session_state.chat = []
    st.sidebar.success("Memory cleared")
    st.rerun()

# ================= CHAT DISPLAY =================

for msg in st.session_state.chat:
    role = "You" if msg["role"] == "user" else "AI"
    st.markdown(f"**{role}:** {msg['content']}")

st.divider()

# ================= CHATGPT-LIKE UPLOAD =================

st.markdown("#### 📎 Attach files or images (optional)")

uploaded_files = st.file_uploader(
    "",
    type=["txt", "pdf", "csv", "png", "jpg", "jpeg"],
    accept_multiple_files=True
)

if uploaded_files:
    st.markdown("**Attached:**")
    for f in uploaded_files:
        if f.type.startswith("image/"):
            st.image(f, width=120)
        else:
            st.markdown(f"📄 {f.name}")

# ================= INPUT =================

with st.form("chat_form", clear_on_submit=True):
    user_msg = st.text_input("Ask something…")
    send = st.form_submit_button("Send")

# ================= UPLOAD PROCESSING =================

def process_uploads(files):
    text_context = ""
    images = []

    for file in files or []:
        if file.type.startswith("image/"):
            images.append({
                "mime_type": file.type,
                "data": file.getvalue()
            })

        elif file.type == "text/plain":
            text_context += file.read().decode("utf-8") + "\n"

        elif file.type == "text/csv":
            text_context += file.read().decode("utf-8") + "\n"

        elif file.type == "application/pdf":
            reader = PyPDF2.PdfReader(file)
            for page in reader.pages:
                text_context += (page.extract_text() or "") + "\n"

    return text_context[:5000], images

# ================= PROMPT =================

def build_prompt(memory, chat, language, file_text):
    lang_inst = "Respond in Hindi." if language == "Hindi" else "Respond in English."

    combined = memory + chat
    recent = combined[-MAX_CONTEXT:]

    body = "\n".join(
        f"{m['role'].upper()}: {m['content']}"
        for m in recent
    )

    file_block = f"\n\nUSER ATTACHMENTS:\n{file_text}" if file_text else ""

    return f"{lang_inst}\n{body}{file_block}"

# ================= CHAT LOGIC =================

if send and user_msg.strip():
    memory = load_memory()

    if not memory:
        memory.append({
            "role": "system",
            "content": (
                "You are a helpful assistant with long-term memory. "
                "Use uploaded files only when relevant."
            )
        })

    st.session_state.chat.append({"role": "user", "content": user_msg})

    file_text, images = process_uploads(uploaded_files)

    prompt = build_prompt(
        memory,
        st.session_state.chat,
        st.session_state.language,
        file_text
    )

    contents = [prompt] + images

    response = client.models.generate_content(
        model=MODEL,
        contents=contents
    )

    reply = response.text.strip()

    st.session_state.chat.append({"role": "assistant", "content": reply})
    st.session_state.speak_now = True

    memory.append({"role": "user", "content": user_msg})
    memory.append({"role": "assistant", "content": reply})
    save_memory(memory)

    st.rerun()

# ================= VOICE OUTPUT =================

def clean_for_voice(text):
    for ch in ["#", "*", "_", "`", ">", "-", "\n"]:
        text = text.replace(ch, " ")
    return " ".join(text.split())

if (
    st.session_state.voice
    and st.session_state.speak_now
    and st.session_state.chat
    and st.session_state.chat[-1]["role"] == "assistant"
):
    speak_text = clean_for_voice(st.session_state.chat[-1]["content"])
    lang = "hi-IN" if st.session_state.language == "Hindi" else "en-US"

    st.components.v1.html(
        f"""
        <script>
        const u = new SpeechSynthesisUtterance({json.dumps(speak_text)});
        u.lang = "{lang}";
        window.speechSynthesis.cancel();
        window.speechSynthesis.speak(u);
        </script>
        """,
        height=0
    )

    st.session_state.speak_now = False

# ================= FOOTER =================

st.divider()
st.markdown(
    """
**Why this instead of ChatGPT**
- Persistent, user-controlled memory  
- ChatGPT-style multimodal uploads  
- Hindi-first accessibility  
- Voice as optional interface  
- Designed for trust, not gimmicks
"""
)
