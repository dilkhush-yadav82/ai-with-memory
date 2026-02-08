import streamlit as st
import json
from pathlib import Path
from google import genai
from google.genai import types
import pandas as pd

# ================= CONFIG =================

st.set_page_config(
    page_title="AI Assistant with Memory",
    page_icon="🧠",
    layout="wide"
)

client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
MODEL = "models/gemini-flash-latest"
MEMORY_FILE = "conversation_history.json"
MAX_CONTEXT = 20

# ================= MEMORY =================

def load_memory():
    if Path(MEMORY_FILE).exists():
        return json.load(open(MEMORY_FILE, "r", encoding="utf-8"))
    return []

def save_memory(mem):
    json.dump(mem, open(MEMORY_FILE, "w", encoding="utf-8"), indent=2)

def clear_memory():
    save_memory([])

# ================= SESSION =================

if "chat" not in st.session_state:
    st.session_state.chat = []

# ================= MEMORY ANALYSIS =================

def extract_facts(memory):
    facts = []
    for m in memory:
        if "name" in m["content"].lower():
            facts.append(m["content"])
        if "like" in m["content"].lower():
            facts.append(m["content"])
    return facts[:5]

# ================= SIDEBAR =================

st.sidebar.title("🧾 User Profile")

memory = load_memory()
facts = extract_facts(memory)

if facts:
    for f in facts:
        st.sidebar.markdown(f"- {f}")
else:
    st.sidebar.info("No personal facts learned yet.")

st.sidebar.divider()

st.sidebar.subheader("🧠 Memory Controls")

if st.sidebar.button("Clear Memory"):
    clear_memory()
    st.session_state.chat = []
    st.sidebar.success("Memory cleared")
    st.rerun()

st.sidebar.download_button(
    "Download Memory",
    data=json.dumps(memory, indent=2),
    file_name="memory.json"
)

# ================= MAIN UI =================

st.title("🧠 AI Assistant with Memory")
st.caption("Transparent memory • Multimodal • Session-aware")

for msg in st.session_state.chat:
    if msg["role"] == "user":
        st.markdown(f"**You:** {msg['content']}")
    else:
        st.markdown(f"**AI:** {msg['content']}")

st.divider()

# ================= INPUT =================

with st.form("chat_form", clear_on_submit=True):
    user_msg = st.text_input("Ask the assistant")

    col1, col2 = st.columns(2)
    image = col1.file_uploader("📷 Image", type=["png", "jpg"])
    file = col2.file_uploader("📄 File", type=["txt", "csv", "pdf"])

    send = st.form_submit_button("Ask Assistant")

# ================= CHAT LOGIC =================

def build_prompt(mem, chat):
    combined = mem + chat
    recent = combined[-MAX_CONTEXT:]
    return "\n".join(
        f"{m['role'].upper()}: {m['content']}" for m in recent
    )

def extract_file(file):
    if file.type == "text/plain":
        return file.read().decode()
    if file.type == "text/csv":
        return pd.read_csv(file).head(20).to_string()
    return "User uploaded a document."

if send and user_msg.strip():
    memory = load_memory()

    if not memory:
        memory.append({
            "role": "system",
            "content": "You are a helpful assistant with long-term memory."
        })

    st.session_state.chat.append({"role": "user", "content": user_msg})

    prompt = build_prompt(memory, st.session_state.chat)
    contents = [prompt]

    if file:
        contents.append(extract_file(file))

    if image:
        contents.append(
            types.Part.from_bytes(image.read(), image.type)
        )

    response = client.models.generate_content(
        model=MODEL,
        contents=contents
    )

    reply = response.text.strip()

    st.session_state.chat.append({"role": "assistant", "content": reply})

    memory.append({"role": "user", "content": user_msg})
    memory.append({"role": "assistant", "content": reply})
    save_memory(memory)

    st.rerun()

# ================= EXPLAINABILITY =================

with st.expander("🤔 Why did I answer this way?"):
    st.markdown("I used the following memory:")
    st.json(memory[-6:])
