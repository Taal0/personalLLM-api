import json
from collections.abc import AsyncIterator

from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse

from app.config import OLLAMA_HOST, OLLAMA_MODEL, PERSONA_BASE_PATH, PERSONA_SURVEY_PATH
from app.ollama import chat as ollama_chat
from app.ollama import chat_stream as ollama_chat_stream
from app.persona import build_messages, load_persona
from app.schemas import ChatRequest, ChatResponse
from app.session_store import append_turn, get_history, resolve_session

app = FastAPI(
    title="Personal LLM API",
    description="Kişisel asistan API — Ollama proxy + RAG (Faz 1)",
    version="0.1.0",
)


def _prepare_chat(body: ChatRequest) -> tuple[str, list[dict[str, str]]]:
    session_id = resolve_session(body.session_id, body.new_session)
    history = get_history(session_id) or []
    messages = build_messages(body.message, history)
    return session_id, messages


@app.get("/health")
def health():
    persona_ok = False
    try:
        load_persona()
        persona_ok = True
    except FileNotFoundError:
        pass

    return {
        "status": "ok",
        "ollama_host": OLLAMA_HOST,
        "ollama_model": OLLAMA_MODEL,
        "persona_base": PERSONA_BASE_PATH,
        "persona_survey": PERSONA_SURVEY_PATH,
        "persona_loaded": persona_ok,
    }


@app.post("/chat", response_model=ChatResponse)
async def chat(body: ChatRequest):
    try:
        session_id, messages = _prepare_chat(body)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    data = await ollama_chat(messages)
    reply = data.get("message", {}).get("content", "")
    append_turn(session_id, body.message, reply)
    return ChatResponse(
        reply=reply,
        model=data.get("model", OLLAMA_MODEL),
        session_id=session_id,
    )


async def _stream_events(
    body: ChatRequest,
    session_id: str,
    messages: list[dict[str, str]],
) -> AsyncIterator[str]:
    yield json.dumps({"type": "session", "session_id": session_id}, ensure_ascii=False) + "\n"

    reply_parts: list[str] = []
    model = OLLAMA_MODEL

    try:
        async for chunk in ollama_chat_stream(messages):
            content = chunk.get("message", {}).get("content", "")
            if content:
                reply_parts.append(content)
                yield json.dumps({"type": "token", "content": content}, ensure_ascii=False) + "\n"
            if chunk.get("done"):
                model = chunk.get("model", OLLAMA_MODEL)
    except HTTPException as exc:
        detail = exc.detail if isinstance(exc.detail, str) else str(exc.detail)
        yield json.dumps({"type": "error", "detail": detail}, ensure_ascii=False) + "\n"
        return

    append_turn(session_id, body.message, "".join(reply_parts))
    yield json.dumps({"type": "done", "model": model}, ensure_ascii=False) + "\n"


@app.post("/chat/stream")
async def chat_stream(body: ChatRequest):
    try:
        session_id, messages = _prepare_chat(body)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return StreamingResponse(
        _stream_events(body, session_id, messages),
        media_type="application/x-ndjson",
    )
