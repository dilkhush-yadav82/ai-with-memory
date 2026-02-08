import streamlit as st
import json
from pathlib import Path
from google import genai
import base64

# ================= PAGE CONFIG =================

st.set_page_config(
    page_title="AI Assistant with Memory",
    page_icon="🧠",
    layout="wide"
)

st.title("🧠 AI Assistant with Memory")
st.caption("Transparent memory • Hindi support • Multimodal assistant")

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

if "uploaded_context" not in st.session_state:
    st.session_state.uploaded_context = ""

# ================= SIDEBAR =================

st.sidebar.title("⚙️ Settings")

st.sidebar.subheader("🌐 Language")
st.session_state.language = st.sidebar.radio(
    "Response language",
    ["English", "Hindi"]
)

st.sidebar.subheader("🔊 Voice Output")
st.session_state.voice = st.sidebar.checkbox(
    "Speak responses",
    value=st.session_state.voice
)

if not st.session_state.voice:
    st.components.v1.html(
        "<script>window.speechSynthesis.cancel();</script>",
        height=0
    )

st.sidebar.divider()

# ---------- File Upload ----------
st.sidebar.subheader("📄 Upload File")
uploaded_file = st.sidebar.file_uploader(
    "TXT / PDF / CSV",
    type=["txt", "pdf", "csv"]
)

if uploaded_file:
    try:
        if uploaded_file.type == "text/plain":
            st.session_state.uploaded_context = uploaded_file.read().decode("utf-8")

        elif uploaded_file.type == "text/csv":
            st.session_state.uploaded_context = uploaded_file.read().decode("utf-8")

        elif uploaded_file.type == "application/pdf":
            import PyPDF2
            reader = PyPDF2.PdfReader(uploaded_file)
            text = ""
            for page in reader.pages:
                text += page.extract_text() or ""
            st.session_state.uploaded_context = text

        st.sidebar.success("File loaded for reasoning (session only)")
    except Exception:
        st.sidebar.error("Failed to read file")

# ---------- Image Upload ----------
st.sidebar.subheader("🖼️ Upload Image")
uploaded_image = st.sidebar.file_uploader(
    "Image (JPG / PNG)",
    type=["jpg", "jpeg", "png"]
)

if uploaded_image:
    st.sidebar.image(uploaded_image, caption="Uploaded image", use_column_width=True)

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

# ================= INPUT =================

with st.form("chat_form", clear_on_submit=True):
    user_msg = st.text_input("Ask the assistant")
    send = st.form_submit_button("Ask Assistant")

# ================= CHAT LOGIC =================

def build_prompt(mem, chat, language, file_context):
    lang_inst = "Respond in Hindi." if language == "Hindi" else "Respond in English."

    combined = mem + chat
    recent = combined[-MAX_CONTEXT:]

    body = "\n".join(
        f"{m['role'].upper()}: {m['content']}" for m in recent
    )

    file_block = ""
    if file_context:
        file_block = f"\n\nUSER PROVIDED FILE CONTENT:\n{file_context[:4000]}"

    return f"{lang_inst}\n{body}{file_block}"

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

    prompt = build_prompt(
        memory,
        st.session_state.chat,
        st.session_state.language,
        st.session_state.uploaded_context
    )

    response = client.models.generate_content(
        model=MODEL,
        contents=prompt
    )

    reply = response.text.strip()

    st.session_state.chat.append({"role": "assistant", "content": reply})
    st.session_state.speak_now = True

    memory.append({"role": "user", "content": user_msg})
    memory.append({"role": "assistant", "content": reply})
    save_memory(memory)

    st.rerun()

# ================= VOICE OUTPUT (FIXED) =================

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
    last = st.session_state.chat[-1]
    speak_text = clean_for_voice(last["content"])

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
- Multimodal reasoning (files & images)
- Hindi-first accessibility
- Voice as an optional interface
- Designed for trust, not gimmicks
"""
)
