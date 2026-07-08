import json
from collections.abc import AsyncIterator

import httpx
from fastapi import HTTPException

from app.config import OLLAMA_HOST, OLLAMA_MODEL, OLLAMA_TEMPERATURE


def _chat_payload(messages: list[dict[str, str]], *, stream: bool) -> dict:
    payload = {
        "model": OLLAMA_MODEL,
        "messages": messages,
        "stream": stream,
        "think": False,
        "options": {"temperature": OLLAMA_TEMPERATURE},
    }
    return payload


def _raise_httpx_error(exc: Exception) -> None:
    if isinstance(exc, httpx.ConnectError):
        raise HTTPException(
            status_code=502,
            detail=f"Ollama'ya bağlanılamadı ({OLLAMA_HOST})",
        ) from exc
    if isinstance(exc, httpx.TimeoutException):
        raise HTTPException(
            status_code=504,
            detail="Ollama yanıt vermedi (timeout)",
        ) from exc
    if isinstance(exc, httpx.HTTPStatusError):
        raise HTTPException(
            status_code=502,
            detail=f"Ollama hatası: {exc.response.text}",
        ) from exc
    raise exc


async def chat(messages: list[dict[str, str]]) -> dict:
    url = f"{OLLAMA_HOST.rstrip('/')}/api/chat"

    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(url, json=_chat_payload(messages, stream=False))
            response.raise_for_status()
            return response.json()
    except (httpx.ConnectError, httpx.TimeoutException, httpx.HTTPStatusError) as exc:
        _raise_httpx_error(exc)


async def chat_stream(messages: list[dict[str, str]]) -> AsyncIterator[dict]:
    url = f"{OLLAMA_HOST.rstrip('/')}/api/chat"

    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            async with client.stream(
                "POST",
                url,
                json=_chat_payload(messages, stream=True),
            ) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if line.strip():
                        yield json.loads(line)
    except (httpx.ConnectError, httpx.TimeoutException, httpx.HTTPStatusError) as exc:
        _raise_httpx_error(exc)
