"""Study notes: a small rich-text document per note, grouped into
VS Code-style expandable subject folders.

Notes store their body as a sanitized slice of HTML (bold/highlight marks
survive, nothing else does) so the browser's contenteditable + execCommand
can be trusted without letting arbitrary markup or scripts through.
"""

from __future__ import annotations

import datetime
import html
import re
import uuid
from html.parser import HTMLParser
from typing import Any

from uniflow.services.common import text, set_feedback, toast

EMPTY_NOTE: dict[str, Any] = {
    "id": "",
    "title": "",
    "subject": "",
    "content": "",
    "tags": [],
    "pinned": False,
    "updated_at": "",
}

UNFILED = "Unfiled"

FONT_FAMILIES: dict[str, str] = {
    "serif": "var(--display)",
    "sans": "var(--body)",
    "mono": "var(--mono)",
}
FONT_FAMILY_LABELS: dict[str, str] = {"serif": "Serif (default)", "sans": "Sans", "mono": "Mono"}

FONT_SIZES: dict[str, str] = {"sm": "0.95rem", "md": "1.05rem", "lg": "1.2rem", "xl": "1.4rem"}
FONT_SIZE_LABELS: dict[str, str] = {"sm": "Small", "md": "Medium (default)", "lg": "Large", "xl": "Extra large"}

_ALLOWED_TAGS = {"b", "strong", "i", "em", "u", "mark", "br", "div", "p", "ul", "ol", "li", "span"}
_VOID_TAGS = {"br"}
# Only a bare "background-color: <hex|word|rgb()>" survives — enough for the
# highlighter tool (execCommand emits rgb()), not enough to smuggle in
# url()/expression()/javascript:.
_BG_STYLE_RE = re.compile(
    r"^background-color:\s*"
    r"(#[0-9a-fA-F]{3,8}|[a-zA-Z]+|rgba?\(\s*\d{1,3}(\s*,\s*\d{1,3}){2}(\s*,\s*(0|1|0?\.\d+))?\s*\))"
    r"\s*;?$"
)


class _BodySanitizer(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.out: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag not in _ALLOWED_TAGS:
            return
        if tag in _VOID_TAGS:
            self.out.append("<br>")
            return
        style = ""
        if tag in ("span", "mark"):
            for name, value in attrs:
                if name == "style" and value and _BG_STYLE_RE.match(value.strip()):
                    style = f' style="{value.strip()}"'
                    break
        self.out.append(f"<{tag}{style}>")

    def handle_endtag(self, tag: str) -> None:
        if tag in _ALLOWED_TAGS and tag not in _VOID_TAGS:
            self.out.append(f"</{tag}>")

    def handle_data(self, data: str) -> None:
        self.out.append(html.escape(data))


def sanitize_body(raw: str) -> str:
    parser = _BodySanitizer()
    parser.feed(raw or "")
    parser.close()
    return "".join(parser.out)


def plain_lines(body_html: str) -> list[str]:
    """Break a note's sanitized HTML body into plain-text lines, one per
    block/line-break, for callers (like flashcard auto-generation) that need
    to read it line by line rather than as one blob."""
    text_ = re.sub(r"<br\s*/?>", "\n", body_html or "", flags=re.IGNORECASE)
    text_ = re.sub(r"</(p|div|li)>", "\n", text_, flags=re.IGNORECASE)
    text_ = re.sub(r"<[^>]+>", "", text_)
    text_ = html.unescape(text_)
    return [line.strip() for line in text_.split("\n") if line.strip()]


def _snippet(body_html: str, length: int = 140) -> str:
    plain = re.sub(r"<[^>]+>", " ", body_html or "")
    plain = re.sub(r"\s+", " ", plain).strip()
    return plain[:length] + ("…" if len(plain) > length else "")


def _word_count(body_html: str) -> int:
    plain = re.sub(r"<[^>]+>", " ", body_html or "")
    return len([w for w in plain.split() if w.strip()])


def _parse_tags(raw: str) -> list[str]:
    seen: set[str] = set()
    tags: list[str] = []
    for part in raw.split(","):
        tag = part.strip()
        key = tag.lower()
        if tag and key not in seen:
            seen.add(key)
            tags.append(tag)
    return tags


def _folder_key(note: dict[str, Any]) -> str:
    return note["subject"] or UNFILED


def _expand(section: dict[str, Any], key: str) -> None:
    if key not in section["expanded_subjects"]:
        section["expanded_subjects"].append(key)


def clear_feedback(data: dict[str, Any]) -> None:
    set_feedback(data["notes"], "", "")


def select_note(data: dict[str, Any], payload: dict[str, Any]) -> None:
    section = data["notes"]
    note_id = text(payload, "note_id")
    section["selected_note_id"] = note_id
    note = next((n for n in section["items"] if n["id"] == note_id), None)
    if note is not None:
        _expand(section, _folder_key(note))


def new_note(data: dict[str, Any]) -> None:
    section = data["notes"]
    note = dict(EMPTY_NOTE)
    note["id"] = str(uuid.uuid4())
    note["title"] = "Untitled note"
    note["updated_at"] = datetime.datetime.now().isoformat(timespec="minutes")
    section["items"].insert(0, note)
    section["selected_note_id"] = note["id"]
    # A leftover search would otherwise hide the tree (and the note we just
    # opened for editing) behind a stale flat results list.
    section["search"] = ""
    _expand(section, UNFILED)
    set_feedback(section, "", "")


def submit(data: dict[str, Any], payload: dict[str, Any]) -> dict[str, str] | None:
    section = data["notes"]
    note = next(
        (n for n in section["items"] if n["id"] == section["selected_note_id"]), None
    )
    if note is None:
        return toast("Open or create a note first.", "warning")

    note["title"] = text(payload, "title") or "Untitled note"
    note["subject"] = text(payload, "subject")
    note["content"] = sanitize_body(payload.get("content", ""))
    note["tags"] = _parse_tags(text(payload, "tags"))
    note["updated_at"] = datetime.datetime.now().isoformat(timespec="minutes")
    _expand(section, _folder_key(note))

    # No toast here: saving now happens automatically and frequently
    # (autosave on every edit, plus on blur/navigation), so popping a
    # notification each time would be constant noise rather than useful
    # feedback.
    return None


def delete(data: dict[str, Any], note_id: str) -> dict[str, str] | None:
    section = data["notes"]
    removed = next((n for n in section["items"] if n["id"] == note_id), None)
    section["items"] = [n for n in section["items"] if n["id"] != note_id]
    if section["selected_note_id"] == note_id:
        section["selected_note_id"] = ""
    if removed is None:
        return None
    set_feedback(section, f"Note deleted: {removed['title']}", "info")
    return toast(f"Deleted note: {removed['title']}", "info")


def toggle_pin(data: dict[str, Any], note_id: str) -> None:
    for note in data["notes"]["items"]:
        if note["id"] == note_id:
            note["pinned"] = not note["pinned"]
            return


def toggle_folder(data: dict[str, Any], payload: dict[str, Any]) -> None:
    section = data["notes"]
    key = text(payload, "subject") or UNFILED
    expanded = section["expanded_subjects"]
    if key in expanded:
        section["expanded_subjects"] = [k for k in expanded if k != key]
    else:
        expanded.append(key)


def set_view(data: dict[str, Any], payload: dict[str, Any]) -> None:
    section = data["notes"]
    if "search" in payload:
        section["search"] = text(payload, "search")


def set_font(data: dict[str, Any], payload: dict[str, Any]) -> None:
    section = data["notes"]
    if "font_family" in payload:
        value = text(payload, "font_family", "serif")
        if value in FONT_FAMILIES:
            section["font_family"] = value
    if "font_size" in payload:
        value = text(payload, "font_size", "md")
        if value in FONT_SIZES:
            section["font_size"] = value


# --- computed values -------------------------------------------------------


def _sorted(notes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    result = sorted(notes, key=lambda n: n["updated_at"], reverse=True)
    result.sort(key=lambda n: n["pinned"], reverse=True)
    return result


def _with_snippet(notes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [{**n, "snippet": _snippet(n["content"])} for n in notes]


def _tree(section: dict[str, Any]) -> list[dict[str, Any]]:
    groups: dict[str, list[dict[str, Any]]] = {}
    for note in section["items"]:
        groups.setdefault(_folder_key(note), []).append(note)

    ordered_keys = sorted(k for k in groups if k != UNFILED)
    if UNFILED in groups:
        ordered_keys.append(UNFILED)

    return [
        {
            "subject": key,
            "notes": _with_snippet(_sorted(groups[key])),
            "expanded": key in section["expanded_subjects"],
        }
        for key in ordered_keys
    ]


def _search_results(section: dict[str, Any]) -> list[dict[str, Any]]:
    query = section["search"].strip().lower()
    if not query:
        return []
    matches = [
        n
        for n in section["items"]
        if query in n["title"].lower()
        or query in _snippet(n["content"], 10_000).lower()
        or any(query in tag.lower() for tag in n.get("tags", []))
    ]
    return _with_snippet(_sorted(matches))


def view(data: dict[str, Any]) -> dict[str, Any]:
    section = data["notes"]
    items = section["items"]
    selected = next(
        (n for n in items if n["id"] == section["selected_note_id"]), None
    )
    family = section["font_family"]
    size = section["font_size"]
    return {
        "tree": _tree(section),
        "search": section["search"],
        "search_results": _search_results(section),
        "total_count": len(items),
        "selected_note_id": section["selected_note_id"],
        "selected_note": selected if selected is not None else dict(EMPTY_NOTE),
        "word_count": _word_count(selected["content"]) if selected is not None else 0,
        "font_family": family,
        "font_size": size,
        "font_family_css": FONT_FAMILIES[family],
        "font_size_css": FONT_SIZES[size],
        "font_family_options": [
            {"value": k, "label": v} for k, v in FONT_FAMILY_LABELS.items()
        ],
        "font_size_options": [
            {"value": k, "label": v} for k, v in FONT_SIZE_LABELS.items()
        ],
        "feedback": section["feedback"],
    }
