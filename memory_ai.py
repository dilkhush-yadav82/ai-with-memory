"""
AI with Memory (Gemini - Local CLI)
==================================
Working, verified Gemini version.
"""

import os
import json
from pathlib import Path
from google import genai

# -------- CONFIG --------

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
MODEL = "models/gemini-flash-latest"
HISTORY_FILE = "conversation_history.json"
MAX_HISTORY = 20

# -------- MEMORY --------

def load_history():
    if Path(HISTORY_FILE).exists():
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_history(h):
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(h, f, indent=2, ensure_ascii=False)

def trim(h):
    if len(h) <= MAX_HISTORY:
        return h
    if h and h[0]["role"] == "system":
        return [h[0]] + h[-(MAX_HISTORY - 1):]
    return h[-MAX_HISTORY:]

# -------- CHAT --------

def chat(user_msg, history):
    if not history:
        history.append({
            "role": "system",
            "content": "You are a helpful AI assistant with memory."
        })

    history.append({"role": "user", "content": user_msg})

    prompt = "\n".join(
        f"{m['role'].upper()}: {m['content']}"
        for m in trim(history)
    )

    response = client.models.generate_content(
        model=MODEL,
        contents=prompt
    )

    reply = response.text.strip()
    history.append({"role": "assistant", "content": reply})
    return reply

# -------- CLI --------

def main():
    print("=" * 60)
    print("AI with Memory (Gemini - Local CLI)")
    print("=" * 60)
    print("Commands: clear memory | show memory | quit")

    history = load_history()

    while True:
        msg = input("\nYou: ").strip()

        if msg.lower() in ("quit", "exit", "q"):
            save_history(history)
            print("💾 Saved. Bye!")
            break

        if msg == "clear memory":
            history = []
            save_history(history)
            print("✨ Memory cleared")
            continue

        if msg == "show memory":
            print(history)
            continue

        reply = chat(msg, history)
        print("\nAI:", reply)
        save_history(history)

if __name__ == "__main__":
    main()
