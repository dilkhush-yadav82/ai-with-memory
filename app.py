import streamlit as st
import json
from pathlib import Path
from google import genai

# ================= PAGE CONFIG =================

st.set_page_config(
    page_title="AI Assistant with Memory",
    page_icon="🧠",
    layout="wide"
)

st.title("🧠 AI Assistant with Memory")
st.caption("Transparent memory • Hindi support • Task-oriented assistant")

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

# 🔑 voice trigger flag (IMPORTANT FIX)
if "speak_now" not in st.session_state:
    st.session_state.speak_now = False

# ================= MEMORY ANALYSIS =================

def extract_profile(memory):
    facts = []
    for m in memory:
        text = m["content"].lower()
        if any(k in text for k in ["name", "naam", "like", "pasand"]):
            facts.append(m["content"])
    return facts[:5]

# ================= SIDEBAR =================

st.sidebar.title("🧾 User Profile")

memory = load_memory()
facts = extract_profile(memory)

if facts:
    for f in facts:
        st.sidebar.markdown(f"- {f}")
else:
    st.sidebar.info("No personal facts learned yet")

st.sidebar.divider()

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

# 🔇 Stop speech immediately if voice is turned OFF
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

st.sidebar.download_button(
    "📥 Download Memory",
    data=json.dumps(memory, indent=2),
    file_name="memory.json"
)

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

def build_prompt(mem, chat, language):
    system = "Respond in Hindi." if language == "Hindi" else "Respond in English."

    combined = mem + chat
    recent = combined[-MAX_CONTEXT:]

    body = "\n".join(
        f"{m['role'].upper()}: {m['content']}" for m in recent
    )

    return f"{system}\n{body}"

if send and user_msg.strip():
    memory = load_memory()

    if not memory:
        memory.append({
            "role": "system",
            "content": (
                "You are a personal assistant with persistent memory. "
                "Remember user facts across sessions."
            )
        })

    st.session_state.chat.append({"role": "user", "content": user_msg})

    prompt = build_prompt(memory, st.session_state.chat, st.session_state.language)

    response = client.models.generate_content(
        model=MODEL,
        contents=prompt
    )

    reply = response.text.strip()

    st.session_state.chat.append({"role": "assistant", "content": reply})

    # 🔊 trigger voice ONLY for this response
    st.session_state.speak_now = True

    memory.append({"role": "user", "content": user_msg})
    memory.append({"role": "assistant", "content": reply})
    save_memory(memory)

    st.rerun()

# ================= EXPLAINABILITY =================

with st.expander("🤔 Why did I answer this way?"):
    st.markdown("Used recent memory:")
    st.json(memory[-6:])

# ================= VOICE OUTPUT (FIXED) =================

if (
    st.session_state.voice
    and st.session_state.speak_now
    and st.session_state.chat
    and st.session_state.chat[-1]["role"] == "assistant"
):
    last = st.session_state.chat[-1]

    lang = "hi-IN" if st.session_state.language == "Hindi" else "en-US"

    st.components.v1.html(
        f"""
        <script>
        const msg = new SpeechSynthesisUtterance({json.dumps(last["content"])});
        msg.lang = "{lang}";
        window.speechSynthesis.cancel();
        window.speechSynthesis.speak(msg);
        </script>
        """,
        height=0
    )

    # 🔒 reset trigger so it NEVER replays
    st.session_state.speak_now = False

# ================= FOOTER =================

st.divider()
st.markdown(
    """
**Why this instead of ChatGPT**
- Persistent, user-controlled memory
- Transparent reasoning
- Hindi-first accessibility
- Voice as an interface, not a gimmick
- Designed as an assistant, not a chatbot
"""
)
