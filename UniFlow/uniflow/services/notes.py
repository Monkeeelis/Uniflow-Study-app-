"""Study notes — small rich-text docs grouped into VS Code-style
collapsible subject folders.

Bodies get stored as sanitized HTML: bold and highlight marks make it
through, everything else gets stripped, which is what lets us trust
contenteditable + execCommand without worrying about stray markup or
script injection.
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
    "pinned": False,
    "updated_at": "",
}

UNFILED = "Unfiled"
# Folder path segments are joined with this, so "Bio/Chapter 1" is a folder
# nested one level inside "Bio". A note's flat "subject" string doubles as
# its full folder path.
PATH_SEP = "/"

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
    # Just an empty buffer to collect the cleaned-up output into.
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.out: list[str] = []

    # Drop anything not on the allowlist; for span/mark, keep the style attr
    # only if it's a safe background-color.
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

    # Same allowlist check, closing side.
    def handle_endtag(self, tag: str) -> None:
        if tag in _ALLOWED_TAGS and tag not in _VOID_TAGS:
            self.out.append(f"</{tag}>")

    # Plain text just gets HTML-escaped and passed through as-is.
    def handle_data(self, data: str) -> None:
        self.out.append(html.escape(data))


# Entry point for cleaning up raw HTML down to the allowed tags/attrs.
def sanitize_body(raw: str) -> str:
    parser = _BodySanitizer()
    parser.feed(raw or "")
    parser.close()
    return "".join(parser.out)


def plain_lines(body_html: str) -> list[str]:
    """Turn a note's HTML body into a list of plain-text lines, split on
    block elements and <br>s — flashcard auto-gen wants it line by line
    rather than as one big blob."""
    text_ = re.sub(r"<br\s*/?>", "\n", body_html or "", flags=re.IGNORECASE)
    text_ = re.sub(r"</(p|div|li)>", "\n", text_, flags=re.IGNORECASE)
    text_ = re.sub(r"<[^>]+>", "", text_)
    text_ = html.unescape(text_)
    return [line.strip() for line in text_.split("\n") if line.strip()]


# Tags stripped, whitespace collapsed, truncated — the preview text shown in note lists.
def _snippet(body_html: str, length: int = 140) -> str:
    plain = re.sub(r"<[^>]+>", " ", body_html or "")
    plain = re.sub(r"\s+", " ", plain).strip()
    return plain[:length] + ("…" if len(plain) > length else "")


# Word count for the editor footer — tags don't count, obviously.
def _word_count(body_html: str) -> int:
    plain = re.sub(r"<[^>]+>", " ", body_html or "")
    return len([w for w in plain.split() if w.strip()])


# No-op if it's already expanded.
def _expand(section: dict[str, Any], key: str) -> None:
    if key not in section["expanded_subjects"]:
        section["expanded_subjects"].append(key)


# Expands a folder path and every ancestor above it, so opening a note three
# folders deep doesn't leave its parent folders collapsed.
def _expand_path(section: dict[str, Any], path: str) -> None:
    if path == UNFILED or not path:
        _expand(section, UNFILED if not path else path)
        return
    parts = path.split(PATH_SEP)
    for i in range(len(parts)):
        _expand(section, PATH_SEP.join(parts[: i + 1]))


# Cleans a user-typed folder name: trims it and strips any "/" so it can't
# masquerade as a deeper path than the caller actually asked for.
def _clean_folder_name(name: str) -> str:
    return name.strip().strip(PATH_SEP)


# Dismiss whatever feedback banner is currently showing.
def clear_feedback(data: dict[str, Any]) -> None:
    set_feedback(data["notes"], "", "")


# User clicked a note — open it and make sure its folder (and every
# ancestor above it) is expanded.
def select_note(data: dict[str, Any], payload: dict[str, Any]) -> None:
    section = data["notes"]
    note_id = text(payload, "note_id")
    section["selected_note_id"] = note_id
    note = next((n for n in section["items"] if n["id"] == note_id), None)
    if note is not None:
        _expand_path(section, note["subject"])


# Fresh untitled note, select it, and clear search so the new note isn't
# hidden behind stale results. An optional "subject" in the payload files it
# straight into that folder (e.g. the "+" on a folder row), otherwise it
# lands in Unfiled.
def new_note(data: dict[str, Any], payload: dict[str, Any] | None = None) -> None:
    section = data["notes"]
    subject = text(payload, "subject") if payload else ""
    note = dict(EMPTY_NOTE)
    note["id"] = str(uuid.uuid4())
    note["title"] = "Untitled note"
    note["subject"] = subject
    note["updated_at"] = datetime.datetime.now().isoformat(timespec="minutes")
    section["items"].insert(0, note)
    section["selected_note_id"] = note["id"]
    # A leftover search would otherwise hide the tree (and the note we just
    # opened for editing) behind a stale flat results list.
    section["search"] = ""
    _expand_path(section, subject)
    set_feedback(section, "", "")


# Registers a new (possibly empty) folder so it shows up in the tree even
# before any note is filed into it. "parent" nests it inside an existing
# folder path; blank parent makes it a top-level folder.
def create_folder(data: dict[str, Any], payload: dict[str, Any]) -> dict[str, str] | None:
    section = data["notes"]
    name = _clean_folder_name(text(payload, "name"))
    if not name:
        return toast("Enter a folder name first.", "warning")
    parent = text(payload, "parent")
    full_path = f"{parent}{PATH_SEP}{name}" if parent else name
    if full_path not in section["folders"]:
        section["folders"].append(full_path)
    _expand_path(section, full_path)
    return None


# Autosave handler, fires on basically every edit to the open note.
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
    note["updated_at"] = datetime.datetime.now().isoformat(timespec="minutes")
    _expand_path(section, note["subject"])

    # No toast here: saving now happens automatically and frequently
    # (autosave on every edit, plus on blur/navigation), so popping a
    # notification each time would be constant noise rather than useful
    # feedback.
    return None


# Deletes by id; also clears the selection if that was the note being viewed.
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


# Just toggles pinned on/off for the given note.
def toggle_pin(data: dict[str, Any], note_id: str) -> None:
    for note in data["notes"]["items"]:
        if note["id"] == note_id:
            note["pinned"] = not note["pinned"]
            return


# Folder header clicked — flip it open/closed.
def toggle_folder(data: dict[str, Any], payload: dict[str, Any]) -> None:
    section = data["notes"]
    key = text(payload, "subject") or UNFILED
    expanded = section["expanded_subjects"]
    if key in expanded:
        section["expanded_subjects"] = [k for k in expanded if k != key]
    else:
        expanded.append(key)


# Search box input, stashed onto the section.
def set_view(data: dict[str, Any], payload: dict[str, Any]) -> None:
    section = data["notes"]
    if "search" in payload:
        section["search"] = text(payload, "search")


# Editor font prefs — only touches whichever of family/size was sent.
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


# Most-recent-first, then pinned notes bubbled above everything else.
def _sorted(notes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    result = sorted(notes, key=lambda n: n["updated_at"], reverse=True)
    result.sort(key=lambda n: n["pinned"], reverse=True)
    return result


# Bolts a "snippet" field onto each note dict for the list view.
def _with_snippet(notes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [{**n, "snippet": _snippet(n["content"])} for n in notes]


def _new_folder_node(name: str, path: str) -> dict[str, Any]:
    return {"name": name, "path": path, "notes": [], "children": {}}


# Builds a nested folder tree keyed by path segment. Every note's subject and
# every explicitly-created (possibly still-empty) folder path gets split on
# "/" and walked into place, creating intermediate folders as needed, so a
# note filed straight into "Bio/Chapter 1" implies a "Bio" folder too even if
# nothing was ever explicitly created there.
def _build_tree(section: dict[str, Any]) -> dict[str, Any]:
    root = _new_folder_node("", "")

    def ensure_path(path: str) -> dict[str, Any]:
        node = root
        parts = path.split(PATH_SEP)
        built = []
        for part in parts:
            built.append(part)
            node = node["children"].setdefault(part, _new_folder_node(part, PATH_SEP.join(built)))
        return node

    for path in section["folders"]:
        ensure_path(path)
    for note in section["items"]:
        if note["subject"]:
            ensure_path(note["subject"])["notes"].append(note)

    return root


# Turns the nested dict built by _build_tree into the sorted list-of-dicts
# shape the frontend renders — folders alphabetical, notes newest/pinned
# first within each one.
def _serialize_tree(node: dict[str, Any], section: dict[str, Any]) -> list[dict[str, Any]]:
    children = sorted(node["children"].values(), key=lambda n: n["name"].lower())
    return [
        {
            "subject": child["path"],
            "name": child["name"],
            "notes": _with_snippet(_sorted(child["notes"])),
            "children": _serialize_tree(child, section),
            "expanded": child["path"] in section["expanded_subjects"],
        }
        for child in children
    ]


# Root-level tree: real folders (possibly nested) first, then the Unfiled
# bucket for subject-less notes pinned to the end.
def _tree(section: dict[str, Any]) -> list[dict[str, Any]]:
    root = _build_tree(section)
    tree = _serialize_tree(root, section)

    unfiled = [n for n in section["items"] if not n["subject"]]
    if unfiled:
        tree.append(
            {
                "subject": UNFILED,
                "name": UNFILED,
                "notes": _with_snippet(_sorted(unfiled)),
                "children": [],
                "expanded": UNFILED in section["expanded_subjects"],
            }
        )
    return tree


# Matches against the title or the body text — whatever's in the search box.
def _search_results(section: dict[str, Any]) -> list[dict[str, Any]]:
    query = section["search"].strip().lower()
    if not query:
        return []
    matches = [
        n
        for n in section["items"]
        if query in n["title"].lower() or query in _snippet(n["content"], 10_000).lower()
    ]
    return _with_snippet(_sorted(matches))


# Pulls together the folder tree, search results, and whatever note is open.
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
