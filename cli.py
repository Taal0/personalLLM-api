#!/usr/bin/env python3
"""Basit terminal istemcisi — Personal LLM API'ye bağlanır."""

import json
import os
import sys
from typing import Optional

import httpx
from dotenv import load_dotenv

load_dotenv()

API_URL = os.environ.get("API_URL", "http://localhost:8000").rstrip("/")

HELP = """Komutlar:
  /new   — yeni oturum (geçmiş sıfırlanır)
  /help  — bu mesaj
  /quit  — çık (veya Ctrl+C / Ctrl+D)"""


def check_health() -> None:
    try:
        with httpx.Client(timeout=5.0) as client:
            response = client.get(f"{API_URL}/health")
            response.raise_for_status()
    except httpx.HTTPError as exc:
        print(f"API'ye bağlanılamadı ({API_URL}): {exc}", file=sys.stderr)
        sys.exit(1)


def stream_chat(
    message: str,
    session_id: Optional[str],
) -> Optional[str]:
    payload: dict = {"message": message}
    if session_id:
        payload["session_id"] = session_id

    try:
        with httpx.Client(timeout=120.0) as client:
            with client.stream("POST", f"{API_URL}/chat/stream", json=payload) as response:
                response.raise_for_status()
                print("Asistan: ", end="", flush=True)
                current_session = session_id

                for line in response.iter_lines():
                    if not line:
                        continue
                    event = json.loads(line)
                    event_type = event.get("type")

                    if event_type == "session":
                        current_session = event.get("session_id")
                    elif event_type == "token":
                        print(event.get("content", ""), end="", flush=True)
                    elif event_type == "error":
                        print(f"\nHata: {event.get('detail', 'bilinmeyen')}", file=sys.stderr)
                        return current_session
                    elif event_type == "done":
                        break

                print()
                return current_session
    except httpx.HTTPError as exc:
        print(f"\nİstek hatası: {exc}", file=sys.stderr)
        return session_id


def main() -> None:
    check_health()
    print(f"Personal LLM — {API_URL}")
    print("Çıkmak için /quit. Yardım: /help\n")

    session_id: Optional[str] = None

    while True:
        try:
            user_input = input("Sen: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGörüşürüz.")
            break

        if not user_input:
            continue

        cmd = user_input.lower()
        if cmd in ("/quit", "/exit", "/q"):
            print("Görüşürüz.")
            break
        if cmd == "/new":
            session_id = None
            print("Yeni oturum.")
            continue
        if cmd == "/help":
            print(HELP)
            continue

        session_id = stream_chat(user_input, session_id)


if __name__ == "__main__":
    main()
