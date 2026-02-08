"""
AI with Memory
===============
A conversational AI that remembers previous interactions.
Uses a local LLM via Ollama (no API key, no billing).

Key Features:
- Remembers conversation history
- Maintains context across sessions
- Personalized responses
- Simple memory management
- Streaming responses (no freezing)
"""

import os
import json
from pathlib import Path
import ollama

# File to store conversation history
HISTORY_FILE = "conversation_history.json"


def load_conversation_history():
    """Load conversation history from file."""
    if Path(HISTORY_FILE).exists():
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return []
    return []


def save_conversation_history(history):
    """Save conversation history to file."""
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2, ensure_ascii=False)


def clear_conversation_history():
    """Delete all conversation history."""
    if Path(HISTORY_FILE).exists():
        os.remove(HISTORY_FILE)
    print("✨ Memory cleared! Starting fresh.")


def display_memory(history):
    """Display the current conversation history."""
    if not history:
        print("No conversation history yet.")
        return

    print("\n" + "=" * 60)
    print("CONVERSATION HISTORY")
    print("=" * 60)

    for i, msg in enumerate(history, 1):
        role = msg["role"].upper()
        content = msg["content"]
        if len(content) > 100:
            content = content[:100] + "..."
        print(f"{i}. [{role}]: {content}")

    print("=" * 60 + "\n")


def trim_history(history, max_messages=20):
    """Keep only recent messages to manage context size."""
    if len(history) <= max_messages:
        return history

    if history and history[0]["role"] == "system":
        return [history[0]] + history[-(max_messages - 1):]
    return history[-max_messages:]


def chat_with_memory(user_message, conversation_history):
    """
    Send a message and get a streamed response with memory.
    """

    # Add system message on first run
    if not conversation_history:
        conversation_history.append({
            "role": "system",
            "content": (
                "You are a helpful AI assistant with memory. "
                "You remember previous parts of the conversation and can reference them. "
                "Be friendly, helpful, and maintain context."
            )
        })

    # Add user message
    conversation_history.append({
        "role": "user",
        "content": user_message
    })

    messages_to_send = trim_history(conversation_history, max_messages=20)

    assistant_message = ""

    # STREAMING RESPONSE (IMPORTANT FIX)
    for chunk in ollama.chat(
        model="phi",   # fast & lightweight
        messages=messages_to_send,
        stream=True
    ):
        token = chunk["message"]["content"]
        print(token, end="", flush=True)
        assistant_message += token

    # Save assistant response
    conversation_history.append({
        "role": "assistant",
        "content": assistant_message
    })

    return assistant_message


def main():
    """Main CLI loop."""
    print("=" * 60)
    print("AI with Memory (Ollama - Local & Free)")
    print("=" * 60)
    print()
    print("I'm an AI assistant that remembers our conversations!")
    print()
    print("Commands:")
    print("  - 'clear memory' : Delete conversation history")
    print("  - 'show memory'  : Display current memory")
    print("  - 'quit'         : Exit")
    print()

    conversation_history = load_conversation_history()

    if conversation_history:
        print(f"📚 Loaded {len(conversation_history)} previous messages")
        print("    (I remember our past conversations!)")
    else:
        print("📝 Starting a new conversation")

    print("\n" + "-" * 60)

    while True:
        user_input = input("\nYou: ").strip()

        if not user_input:
            continue

        if user_input.lower() in ["quit", "exit", "q"]:
            save_conversation_history(conversation_history)
            print("\n💾 Conversation saved. Goodbye!")
            break

        elif user_input.lower() == "clear memory":
            conversation_history = []
            clear_conversation_history()
            continue

        elif user_input.lower() == "show memory":
            display_memory(conversation_history)
            continue

        try:
            print("\nAI: ", end="", flush=True)
            chat_with_memory(user_input, conversation_history)
            print()  # newline after streaming
            save_conversation_history(conversation_history)

        except Exception as e:
            print(f"\n❌ Error: {e}")
            print("Please make sure Ollama is running and the model is installed.")


if __name__ == "__main__":
    main()
