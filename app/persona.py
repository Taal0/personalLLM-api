from pathlib import Path

import yaml

from app.config import PERSONA_BASE_PATH, PERSONA_SURVEY_PATH

_LENGTH_MAP = {
    "kisa": "1-3 sentences",
    "orta": "short paragraph",
    "detayli": "a few paragraphs",
}

_DEPTH_MAP = {
    "minimal": "give only the result, no explanation",
    "orta": "brief explanation, don't go deep",
    "derin": "always explain in detail",
}

_CODE_MAP = {
    "istek_uzerine": "only when the user asks",
    "her_zaman": "always for technical questions",
    "hic": "never provide code examples",
}

_PROACTIVE_MAP = {
    "sorulunca": (
        "Answer only what was asked, then stop. "
        "Do not end with a question. Do not ask counter-questions "
        "(e.g. 'what are you testing?', 'how is it going?', 'what would you like to do?') "
        "unless the user asked something that truly needs one clarifying question."
    ),
    "hafif": "You may occasionally offer brief suggestions, but don't push.",
    "cok": "Actively offer suggestions.",
}

_AVOID_MAP = {
    "emoji": "Don't use emoji",
    "ai_kliseleri": (
        'Avoid AI clichés like "Great question!", "Of course!", "Certainly!", '
        '"Harika!", "Peki," as filler'
    ),
    "gereksiz_motivasyon": "No unnecessary motivational talk",
    "uzun_giris_cumleleri": "No long opening sentences — get to the point",
    "surekli_ozur": 'Don\'t keep saying "sorry"',
    "soruyu_tekrar_etme": "Don't repeat the user's question back",
    "kapanis_onerileri": (
        "Never end with unsolicited closers like 'Dilersen bir sonraki adımda...', "
        "'what would you like to do next?', or 'shall we look at the next step?'"
    ),
    "gereksiz_soru_sorma": (
        "Do not ask the user questions they did not ask for "
        "(e.g. 'Ne test ediyorsun?', 'Nasıl buluyorsun?', 'Ne yapmak istersin?')"
    ),
}

_FOCUS_MAP = {
    "dersler": "university courses",
    "projeler": "personal projects",
    "gunluk_sohbet": "casual chat and brainstorming",
    "kod": "coding and debugging",
    "arastirma": "research and learning",
}

_ROLE_MAP = {
    "bilgisayar mühendisliği öğrencisi": "computer engineering student",
}

_RESPONSE_LANGUAGE = (
    "Always respond in Turkish. Technical terms may remain in English; "
    "occasional extra English words are fine."
)


def _read_file(path: str) -> str:
    p = Path(path)
    if not p.is_file():
        raise FileNotFoundError(f"Dosya bulunamadı: {p}")
    return p.read_text(encoding="utf-8").strip()


def _load_survey() -> dict:
    raw = _read_file(PERSONA_SURVEY_PATH)
    return yaml.safe_load(raw)


def _render_survey(survey: dict) -> str:
    lines: list[str] = []

    addressing = survey.get("addressing", "sen")
    user_name = survey.get("user_name", "")

    if addressing == "isim" and user_name:
        lines.append(
            f'- The user\'s name is {user_name}. Address them by name (e.g. "{user_name}, ..."). '
            f'Never use "sen" as their name — "sen" is only the informal pronoun if needed.'
        )
    elif addressing == "sen":
        lines.append('- Address the user informally with "sen" (Turkish informal you).')
    elif addressing == "siz":
        lines.append('- Address the user formally with "siz" (Turkish formal you).')
    elif user_name:
        lines.append(
            f'- The user\'s name is {user_name}. Address them by name. '
            f'Never confuse "sen" (informal you) with their name.'
        )
    else:
        lines.append(f"- Address the user as: {addressing}.")

    ctx = survey.get("context", {})
    role = ctx.get("role", "")
    if role:
        role_en = _ROLE_MAP.get(role, role)
        lines.append(f"- The user is a {role_en}.")

    focus = survey.get("focus_areas", [])
    if focus:
        areas = ", ".join(_FOCUS_MAP.get(f, f) for f in focus)
        lines.append(f"- Focus areas: {areas}.")

    length = _LENGTH_MAP.get(survey.get("response_length", "kisa"), "1-3 sentences")
    lines.append(
        f"- Default response length: {length}. Expand if the user wants detail. "
        "A short answer must not end with a question just to fill space."
    )

    depth = _DEPTH_MAP.get(survey.get("technical_depth", "orta"), "brief explanation")
    lines.append(f"- Technical depth: {depth}.")

    code = _CODE_MAP.get(survey.get("code_examples", "istek_uzerine"), "only when asked")
    lines.append(f"- Code examples: {code}.")

    proactive = _PROACTIVE_MAP.get(survey.get("proactive", "hafif"), "")
    if proactive:
        lines.append(f"- {proactive}")

    uncertainty = survey.get("uncertainty", "acikca_soyle")
    if uncertainty == "acikca_soyle":
        lines.append('- When unsure, clearly say "emin değilim" (in Turkish).')
    elif uncertainty == "en_iyi_tahmini":
        lines.append("- When unsure, give your best guess and add a warning.")

    avoid_keys = survey.get("avoid", [])
    avoid_lines = [_AVOID_MAP[k] for k in avoid_keys if k in _AVOID_MAP]
    if avoid_lines:
        lines.append("- " + "; ".join(avoid_lines).rstrip(".") + ".")

    lines.append(f"- {_RESPONSE_LANGUAGE}")

    return "\n".join(lines)


def load_persona() -> str:
    base = _read_file(PERSONA_BASE_PATH)
    survey = _load_survey()

    name = survey.get("assistant_name") or "assistant"
    base = base.replace("{name}", name)

    preferences = _render_survey(survey)
    return f"{base}\n\n## User preferences\n{preferences}"


def build_messages(
    user_message: str,
    history: list[dict[str, str]] | None = None,
) -> list[dict[str, str]]:
    messages: list[dict[str, str]] = [{"role": "system", "content": load_persona()}]
    if history:
        messages.extend(history)
    messages.append({"role": "user", "content": user_message})
    return messages
