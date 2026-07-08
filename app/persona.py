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
    "sorulunca": "Answer only what was asked, then stop. No counter-questions unless one clarifying question is truly needed.",
    "hafif": "You may occasionally offer brief suggestions, but don't push.",
    "cok": "Actively offer suggestions.",
}

_AVOID_MAP = {
    "emoji": "No emoji",
    "ai_kliseleri": 'No AI clichés ("Harika!", "Tabii ki!", "Great question!")',
    "gereksiz_motivasyon": "No motivational filler",
    "uzun_giris_cumleleri": "No long openings — get to the point",
    "surekli_ozur": "Don't over-apologize",
    "soruyu_tekrar_etme": "Don't echo the user's question",
    "kapanis_onerileri": "No unsolicited closers ('Ne yapmak istersin?', 'bir sonraki adım...')",
    "gereksiz_soru_sorma": "Don't ask questions the user didn't ask for",
    "asiri_kedi_roleplay": "No meow/nya / cute-kitten spam",
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

_RESPONSE_LANGUAGE = "Reply in Turkish; English tech terms ok."


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
        lines.append(f"- User's name: {user_name}. Address by name; \"sen\" is only the informal you, never their name.")
    elif addressing == "sen":
        lines.append('- Address informally with "sen".')
    elif addressing == "siz":
        lines.append('- Address formally with "siz".')
    elif user_name:
        lines.append(f"- User's name: {user_name}. Address by name.")
    else:
        lines.append(f"- Address as: {addressing}.")

    ctx = survey.get("context", {})
    role = ctx.get("role", "")
    if role:
        role_en = _ROLE_MAP.get(role, role)
        lines.append(f"- The user is a {role_en}.")

    channel = ctx.get("channel", "")
    if channel == "mac_desktop_pet":
        lines.append("- You are Chibi on the Mac desktop pet UI.")
    elif channel:
        lines.append(f"- Channel: {channel}.")

    tone = survey.get("tone", "")
    if tone:
        lines.append(f"- Tone: {tone}.")

    focus = survey.get("focus_areas", [])
    if focus:
        areas = ", ".join(_FOCUS_MAP.get(f, f) for f in focus)
        lines.append(f"- Focus areas: {areas}.")

    length = _LENGTH_MAP.get(survey.get("response_length", "kisa"), "1-3 sentences")
    lines.append(f"- Default length: {length}.")

    depth = _DEPTH_MAP.get(survey.get("technical_depth", "orta"), "brief explanation")
    lines.append(f"- Technical depth: {depth}.")

    code = _CODE_MAP.get(survey.get("code_examples", "istek_uzerine"), "only when asked")
    lines.append(f"- Code: {code}.")

    proactive = _PROACTIVE_MAP.get(survey.get("proactive", "hafif"), "")
    if proactive:
        lines.append(f"- {proactive}")

    uncertainty = survey.get("uncertainty", "acikca_soyle")
    if uncertainty == "acikca_soyle":
        lines.append('- If unsure: say "emin değilim".')
    elif uncertainty == "en_iyi_tahmini":
        lines.append("- If unsure: best guess + warning.")

    avoid_keys = survey.get("avoid", [])
    avoid_lines = [_AVOID_MAP[k] for k in avoid_keys if k in _AVOID_MAP]
    if avoid_lines:
        lines.append("- Avoid: " + "; ".join(avoid_lines).rstrip(".") + ".")

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
