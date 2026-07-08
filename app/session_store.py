import time
import uuid
from dataclasses import dataclass, field

from app.config import MAX_HISTORY_TURNS, SESSION_IDLE_TTL_SECONDS

Message = dict[str, str]


@dataclass
class _Session:
    messages: list[Message] = field(default_factory=list)
    last_access: float = field(default_factory=time.monotonic)


_sessions: dict[str, _Session] = {}


def _is_expired(session: _Session) -> bool:
    if SESSION_IDLE_TTL_SECONDS <= 0:
        return False
    return time.monotonic() - session.last_access > SESSION_IDLE_TTL_SECONDS


def _touch(session: _Session) -> None:
    session.last_access = time.monotonic()


def _trim(messages: list[Message]) -> None:
    max_messages = MAX_HISTORY_TURNS * 2
    if len(messages) > max_messages:
        del messages[: len(messages) - max_messages]


def create_session() -> str:
    session_id = str(uuid.uuid4())
    _sessions[session_id] = _Session()
    return session_id


def get_history(session_id: str) -> list[Message] | None:
    session = _sessions.get(session_id)
    if session is None:
        return None
    if _is_expired(session):
        del _sessions[session_id]
        return None
    _touch(session)
    return list(session.messages)


def append_turn(session_id: str, user: str, assistant: str) -> None:
    session = _sessions.get(session_id)
    if session is None:
        session = _Session()
        _sessions[session_id] = session
    session.messages.append({"role": "user", "content": user})
    session.messages.append({"role": "assistant", "content": assistant})
    _trim(session.messages)
    _touch(session)


def resolve_session(session_id: str | None, new_session: bool) -> str:
    if new_session:
        return create_session()
    if session_id:
        session = _sessions.get(session_id)
        if session is not None and not _is_expired(session):
            _touch(session)
            return session_id
        _sessions.pop(session_id, None)
    return create_session()
