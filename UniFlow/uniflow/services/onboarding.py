"""Onboarding wizard plus the profile settings that reuse the same fields."""

from __future__ import annotations

from typing import Any

from uniflow.services.common import flag, positive_int, text, toast

YEAR_OPTIONS = [
    "High School",
    "Year 11",
    "Year 12",
    "Undergraduate",
    "Postgraduate",
    "Other",
]

THEME_OPTIONS = [
    {"value": "light", "label": "Cream (default)"},
    {"value": "high-contrast", "label": "High Contrast"},
    {"value": "ocean", "label": "Ocean"},
    {"value": "purple", "label": "Purple & Yellow"},
    {"value": "pink", "label": "Pink"},
]

COLORBLIND_OPTIONS = [
    {"value": "none", "label": "Off"},
    {"value": "protanopia", "label": "Protanopia (red-weak)"},
    {"value": "deuteranopia", "label": "Deuteranopia (green-weak)"},
    {"value": "tritanopia", "label": "Tritanopia (blue-weak)"},
    {"value": "deuteranomaly", "label": "Deuteranomaly (green-shifted)"},
    {"value": "achromatopsia", "label": "Achromatopsia (no colour)"},
]

LAST_STEP = 3


def update(data: dict[str, Any], payload: dict[str, Any]) -> None:
    """Partially update the onboarding/profile fields that the wizard and the
    profile settings page share.

    This is the handler behind the ``onboarding/update`` action. It backs
    both the multi-step onboarding wizard (name, year level, pomodoro
    lengths, weekly goal) and the "Profile" settings page, since both UIs
    edit the exact same ``data["onboarding"]`` fields and there is no reason
    to maintain two separate update paths.

    Every field is optional and independent: only keys actually present in
    ``payload`` are touched, so a caller can update just one field (e.g. only
    ``name``) without needing to resend the rest of the profile. This mirrors
    a PATCH semantics rather than a PUT.

    Validation/sanitisation per field:
      - ``name``: coerced to a stripped string via :func:`text`; any string
        is accepted, including an empty one (clearing the name).
      - ``year_level``: coerced to a string via :func:`text`, then only
        written if it is either the empty string or one of the values in
        :data:`YEAR_OPTIONS`. This means an unrecognised value is silently
        dropped rather than raising, which protects against a stale/garbage
        client sending a value that no longer matches the option list.
      - ``pomodoro_work`` / ``pomodoro_break``: coerced with
        :func:`positive_int`, falling back to sensible defaults (25 and 5
        minutes respectively) if the payload value cannot be parsed as a
        positive integer.
      - ``weekly_goal_minutes``: coerced with :func:`positive_int`, falling
        back to 300 minutes (5 hours) if invalid.
      - ``notifications_enabled``: coerced to a real bool via :func:`flag`,
        regardless of whether the client sent a JSON boolean, a string like
        ``"true"``, or a truthy/falsy value.

    Args:
        data: The full application state document (the entire JSON blob
            persisted to disk for this device). This function reads and
            mutates the ``"onboarding"`` sub-dict in place.
        payload: The raw JSON body of the incoming action request. Only the
            keys documented above are ever inspected; unknown keys are
            ignored.

    Returns:
        None. All changes are applied in place to ``data["onboarding"]``;
        the caller (``app.py``'s action dispatcher) is responsible for
        persisting ``data`` afterwards and re-rendering the view model via
        :func:`view`.
    """
    ob = data["onboarding"]
    if "name" in payload:
        ob["name"] = text(payload, "name")
    if "year_level" in payload:
        value = text(payload, "year_level")
        if value in YEAR_OPTIONS or value == "":
            ob["year_level"] = value
    if "pomodoro_work" in payload:
        ob["pomodoro_work"] = positive_int(payload["pomodoro_work"], 25)
    if "pomodoro_break" in payload:
        ob["pomodoro_break"] = positive_int(payload["pomodoro_break"], 5)
    if "weekly_goal_minutes" in payload:
        ob["weekly_goal_minutes"] = positive_int(payload["weekly_goal_minutes"], 300)
    if "notifications_enabled" in payload:
        ob["notifications_enabled"] = flag(payload, "notifications_enabled")


def set_step(data: dict[str, Any], payload: dict[str, Any]) -> None:
    """Advance, rewind, or jump the onboarding wizard to a specific step.

    This single handler backs three different pieces of UI so none of them
    need their own action:
      - The "Next" button, which sends no ``step``/``delta`` at all and
        relies on the default ``delta`` of ``+1``.
      - The "Back" button, which sends ``{"delta": -1}``.
      - The row of clickable step dots at the top of the wizard, which send
        an explicit ``{"step": <index>}`` to jump directly to that step.

    Resolution order:
      1. If ``payload`` contains a ``"step"`` key, that value is used
         directly as the target step (absolute positioning takes priority
         over any relative delta).
      2. Otherwise, a ``"delta"`` is read from the payload (defaulting to
         ``1`` if absent) and added to the current ``ob["step"]`` to compute
         the target.

    Both the ``step`` and ``delta`` values are defensively coerced with
    ``int(...)`` inside ``try``/``except`` blocks: a malformed or
    non-numeric value (e.g. ``None``, ``"abc"``, or a stray object) falls
    back to a safe default (``delta = 1`` for a bad delta, or the current
    step unchanged for a bad absolute step) instead of raising and crashing
    the request.

    The final target step is always clamped with
    ``max(0, min(LAST_STEP, target))`` so the wizard can never be pushed
    before the first step or past the last one, regardless of what the
    client sends.

    Args:
        data: The full application state document; this function reads and
            mutates ``data["onboarding"]["step"]`` in place.
        payload: The raw JSON body of the incoming action request. May
            contain ``"step"`` (absolute target, any int-coercible value) or
            ``"delta"`` (relative movement, any int-coercible value,
            defaulting to ``1``). If both are absent, behaves as "advance by
            one step".

    Returns:
        None. The new step is written directly to
        ``data["onboarding"]["step"]``.
    """
    ob = data["onboarding"]
    if "step" in payload:
        target = payload["step"]
    else:
        try:
            delta = int(payload.get("delta", 1))
        except (TypeError, ValueError):
            delta = 1
        target = ob["step"] + delta
    try:
        target = int(target)
    except (TypeError, ValueError):
        target = ob["step"]
    ob["step"] = max(0, min(LAST_STEP, target))


def add_subject(data: dict[str, Any], payload: dict[str, Any]) -> dict[str, str] | None:
    """Append a new subject/class name to the user's onboarding subject list.

    This backs the "Add subject" input during onboarding (and, if reused, on
    the profile page) where the user types a free-text subject name like
    "Chemistry" or "MTH1030" and it gets added to
    ``data["onboarding"]["subjects"]``, which later feeds subject dropdowns
    across the app (tasks, calendar categories, notes, etc.).

    Two guard conditions prevent bad list entries, each surfaced to the user
    as a warning toast rather than silently failing or raising an exception:
      1. **Empty name**: if, after trimming via :func:`text`, the name is an
         empty string, nothing is added and a "Enter a subject name first."
         warning toast is returned.
      2. **Duplicate name**: if the (case-sensitive, exact-match) name is
         already present in the list, nothing is added and a
         "{name} is already on your list." warning toast is returned. This
         is a simple ``in`` check against the list, not a case-insensitive
         comparison, so "Maths" and "maths" would currently be treated as
         distinct entries.

    If neither guard trips, the name is appended to the end of the list
    (preserving insertion order, which matters for how subjects are later
    displayed) and ``None`` is returned to indicate success with no toast
    needed (the UI will simply show the updated list).

    Args:
        data: The full application state document; this function mutates
            ``data["onboarding"]["subjects"]`` in place by appending to it.
        payload: The raw JSON body of the incoming action request, expected
            to contain a ``"name"`` key with the subject name typed by the
            user.

    Returns:
        A warning :func:`toast` dict (with ``"message"`` and ``"kind"``
        keys) if the name was empty or a duplicate, or ``None`` if the
        subject was added successfully.
    """
    name = text(payload, "name")
    if not name:
        return toast("Enter a subject name first.", "warning")
    subjects = data["onboarding"]["subjects"]
    if name in subjects:
        return toast(f"{name} is already on your list.", "warning")
    subjects.append(name)
    return None


def remove_subject(data: dict[str, Any], name: str) -> None:
    """Remove a subject/class name from the user's onboarding subject list.

    Rebuilds ``data["onboarding"]["subjects"]`` as a new list containing
    every existing subject except the ones that exactly match ``name``
    (case-sensitive string equality, no trimming/normalisation applied here
    since ``name`` is expected to already be one of the exact strings stored
    in the list, e.g. from clicking a specific subject's "remove" button in
    the UI).

    This is intentionally permissive about the "not found" case: if ``name``
    does not match anything in the list, the list comprehension simply keeps
    every existing entry unchanged and no error is raised. There is
    therefore no need for the caller to check existence first, and no toast
    or return value is needed to signal success/failure.

    Args:
        data: The full application state document; this function replaces
            ``data["onboarding"]["subjects"]`` in place with a filtered
            list.
        name: The exact subject name to remove, as previously stored via
            :func:`add_subject`.

    Returns:
        None. The filtered list is written directly back to
        ``data["onboarding"]["subjects"]``.
    """
    ob = data["onboarding"]
    ob["subjects"] = [s for s in ob["subjects"] if s != name]


def toggle_notifications(data: dict[str, Any]) -> None:
    """Flip the master notifications-enabled switch to its opposite state.

    Backs the notifications toggle on the profile settings page. Unlike
    :func:`update`, which can set ``notifications_enabled`` to an explicit
    value sent by the client, this handler takes no payload at all: it is a
    pure boolean flip (``True`` becomes ``False`` and vice versa) driven
    entirely by server-side state, which is the natural semantics for a
    single on/off toggle button that always shows the current state and
    reverses it on click.

    This flag is read elsewhere in the app (see ``services/notifications.py``)
    to decide whether new notifications should actually be created/surfaced
    to the user, or suppressed while the feature is toggled off.

    Args:
        data: The full application state document; this function mutates
            ``data["onboarding"]["notifications_enabled"]`` in place.

    Returns:
        None. The new boolean value is written directly to
        ``data["onboarding"]["notifications_enabled"]``.
    """
    ob = data["onboarding"]
    ob["notifications_enabled"] = not ob["notifications_enabled"]


def toggle_theme(data: dict[str, Any]) -> None:
    """Flip the light/dark mode flag, independently of the chosen colour theme.

    This backs the sun/moon icon button in the navbar (see the
    ``settings/theme/toggle`` action). Despite the function's name, it does
    not change ``data["onboarding"]["theme"]`` (the colour palette, e.g.
    "light", "ocean", "purple", "pink", "high-contrast") — that is a
    separate concern handled by :func:`set_theme`. Instead this only flips
    the boolean ``dark_mode`` flag, which the frontend uses (in combination
    with the colour theme) to pick between a theme's light and dark CSS
    variable sets — e.g. "ocean" + dark mode on renders differently to
    "ocean" + dark mode off, but is still recognisably the "ocean" theme.

    The one exception is the "high-contrast" theme, which the frontend
    treats as having no separate dark variant (it is already maximally
    high-contrast), so toggling this flag while that theme is selected has
    no visible effect, even though the underlying flag still flips.

    Like :func:`toggle_notifications`, this takes no payload since it is a
    simple, unconditional state flip driven by a single-purpose button that
    always represents "switch to the other mode".

    Args:
        data: The full application state document; this function mutates
            ``data["onboarding"]["dark_mode"]`` in place.

    Returns:
        None. The new boolean value is written directly to
        ``data["onboarding"]["dark_mode"]``.
    """
    ob = data["onboarding"]
    ob["dark_mode"] = not ob["dark_mode"]


def set_theme(data: dict[str, Any], payload: dict[str, Any]) -> None:
    """Set the app's colour theme to one of the predefined palette options.

    Backs the "Theme" dropdown on the profile settings page (the
    ``settings/theme/set`` action). ``value`` is coerced to a stripped
    string via :func:`text`, then checked for membership in the set of
    valid values drawn from :data:`THEME_OPTIONS` (currently: ``"light"``,
    ``"high-contrast"``, ``"ocean"``, ``"purple"``, and ``"pink"``).

    If the value is not a recognised theme (e.g. a stale option from an
    older version of the frontend, a typo, or a malicious/malformed
    request), the assignment is silently skipped and
    ``data["onboarding"]["theme"]`` is left completely unchanged — there is
    no fallback-to-default behaviour here, unlike some of the numeric
    fields in :func:`update`. This is a deliberate whitelist check rather
    than a blacklist, so any future addition to :data:`THEME_OPTIONS`
    automatically becomes selectable without touching this function.

    Note that this is orthogonal to :func:`toggle_theme`: this function
    picks the colour palette, while ``dark_mode`` (flipped independently)
    picks whether that palette renders in its light or dark variant.

    Args:
        data: The full application state document; this function
            conditionally mutates ``data["onboarding"]["theme"]`` in place.
        payload: The raw JSON body of the incoming action request, expected
            to contain a ``"theme"`` key with one of the values from
            :data:`THEME_OPTIONS`.

    Returns:
        None. On a valid theme value, it is written directly to
        ``data["onboarding"]["theme"]``; on an invalid value, nothing
        happens.
    """
    value = text(payload, "theme")
    if value in {option["value"] for option in THEME_OPTIONS}:
        data["onboarding"]["theme"] = value


def set_colorblind_mode(data: dict[str, Any], payload: dict[str, Any]) -> None:
    """Set the colour-blindness accessibility adjustment mode for the app.

    Backs the "Colour blind support" dropdown on the profile settings page
    (the ``settings/colorblind/set`` action). This is structurally identical
    to :func:`set_theme` — a whitelist check against a fixed options list —
    but for a completely independent accessibility setting layered on top
    of whichever colour theme is active.

    ``value`` is coerced to a stripped string via :func:`text`, then checked
    for membership in the set of valid values drawn from
    :data:`COLORBLIND_OPTIONS` (currently: ``"none"`` for off, plus
    ``"protanopia"``, ``"deuteranopia"``, ``"tritanopia"``,
    ``"deuteranomaly"``, and ``"achromatopsia"`` for the various forms of
    colour vision deficiency the frontend knows how to compensate for, e.g.
    via CSS filters or an adjusted colour palette).

    If the value is not one of these recognised modes, the assignment is
    silently skipped and ``data["onboarding"]["colorblind_mode"]`` is left
    unchanged, exactly like the invalid-value behaviour in :func:`set_theme`.

    Args:
        data: The full application state document; this function
            conditionally mutates ``data["onboarding"]["colorblind_mode"]``
            in place.
        payload: The raw JSON body of the incoming action request, expected
            to contain a ``"mode"`` key with one of the values from
            :data:`COLORBLIND_OPTIONS`.

    Returns:
        None. On a valid mode value, it is written directly to
        ``data["onboarding"]["colorblind_mode"]``; on an invalid value,
        nothing happens.
    """
    value = text(payload, "mode")
    if value in {option["value"] for option in COLORBLIND_OPTIONS}:
        data["onboarding"]["colorblind_mode"] = value


def finish(data: dict[str, Any], device_id: str) -> dict[str, str]:
    """Mark the onboarding wizard as complete for the current device/browser.

    Called when the user clicks "Get started"/"Finish" on the last step of
    the onboarding wizard (the ``onboarding/finish`` action). Onboarding
    completion is tracked per-device rather than as a single global flag,
    because this app's data model already keys persistence off of a
    per-browser ``device_id`` cookie (see ``store.py``) — but historically
    (and still, for backward compatibility / simplicity of the "has this
    profile ever finished onboarding" question) there is also a single
    global ``ob["completed"]`` flag that this function unconditionally sets
    to ``True``.

    The per-device tracking lives in ``ob["completed_devices"]``, a list of
    device IDs that have each individually finished the wizard. This lets a
    scenario like "the same server-side profile/account is opened from a
    new browser or a re-installed app on the same device" prompt onboarding
    again for that specific device, without resetting or affecting any other
    device's completion status or the user's actual saved profile data
    (name, subjects, pomodoro settings, etc. are untouched here).

    Adding to that list is idempotent and defensive: it only appends
    ``device_id`` if it is a non-empty/truthy string AND not already present
    in the list, so calling ``finish`` multiple times for the same device
    (e.g. a network retry, or the user somehow re-triggering the action)
    never creates duplicate entries.

    Args:
        data: The full application state document; this function mutates
            ``data["onboarding"]["completed"]`` and
            ``data["onboarding"]["completed_devices"]`` in place.
        device_id: The unique identifier for the current browser/device,
            sourced from the ``uniflow_device`` cookie set in ``app.py``.
            May be an empty string in edge cases (e.g. cookies blocked),
            in which case no device-specific tracking occurs but the global
            ``completed`` flag is still set.

    Returns:
        A success :func:`toast` dict containing a personalised greeting
        (``"Welcome, {name}!"``) if the user provided a name during
        onboarding, or a generic ``"Welcome to UniFlow!"`` greeting if they
        did not.
    """
    ob = data["onboarding"]
    ob["completed"] = True
    if device_id and device_id not in ob["completed_devices"]:
        ob["completed_devices"].append(device_id)
    greeting = f"Welcome, {ob['name']}!" if ob["name"] else "Welcome to UniFlow!"
    return toast(greeting, "success")


def view(data: dict[str, Any], device_id: str) -> dict[str, Any]:
    """Build the read-only view model for the onboarding wizard and profile page.

    This is the "GET"-style counterpart to all the mutating functions above:
    it performs no writes to ``data`` and is called after every action (not
    just onboarding-specific ones) to compute the fresh slice of view state
    that the frontend's onboarding wizard and profile settings page render
    from. It follows the same shape/naming pattern as the other services'
    ``view()`` functions (see ``services/tasks.py``, ``services/focus.py``,
    etc.) so the frontend can treat every page's data uniformly.

    Notably, ``"completed"`` here is computed per-device (whether
    ``device_id`` is a member of ``ob["completed_devices"]``) rather than
    simply returning the global ``ob["completed"]`` flag written by
    :func:`finish`. This is what actually drives the "should this specific
    browser see the onboarding wizard or the main app" decision — the global
    flag exists for other/legacy purposes but the per-device check is what
    matters for rendering.

    The returned dict also bundles in the static option lists
    (:data:`YEAR_OPTIONS`, :data:`THEME_OPTIONS`, :data:`COLORBLIND_OPTIONS`)
    alongside the user's current selections, so the frontend doesn't need
    its own hardcoded copies of these lists to populate dropdowns/selects —
    the backend is the single source of truth for what options exist.

    Args:
        data: The full application state document; only read from, never
            mutated.
        device_id: The unique identifier for the current browser/device,
            used solely to compute the per-device ``"completed"`` value by
            checking membership in ``ob["completed_devices"]``.

    Returns:
        A dict containing every field the frontend needs to render the
        onboarding wizard and/or profile settings page:
          - ``completed``: whether *this device* has finished onboarding.
          - ``step`` / ``last_step``: current wizard step and the index of
            the final step, for progress indicators and Next/Back bounds.
          - ``name``, ``year_level``, ``subjects``: the user-entered profile
            fields collected during onboarding.
          - ``year_options``: the fixed list of selectable year levels.
          - ``pomodoro_work``, ``pomodoro_break``, ``weekly_goal_minutes``:
            numeric settings configured during onboarding, also editable
            later from the profile page.
          - ``notifications_enabled``: the master notifications toggle.
          - ``theme`` / ``theme_options``: the active colour theme and the
            full list of themes available to choose from.
          - ``dark_mode``: whether dark mode is layered on top of the
            active theme.
          - ``colorblind_mode`` / ``colorblind_options``: the active
            colour-blindness adjustment and the full list of modes
            available to choose from.
    """
    ob = data["onboarding"]
    return {
        "completed": device_id in ob["completed_devices"],
        "step": ob["step"],
        "last_step": LAST_STEP,
        "name": ob["name"],
        "year_level": ob["year_level"],
        "year_options": YEAR_OPTIONS,
        "subjects": ob["subjects"],
        "pomodoro_work": ob["pomodoro_work"],
        "pomodoro_break": ob["pomodoro_break"],
        "weekly_goal_minutes": ob["weekly_goal_minutes"],
        "notifications_enabled": ob["notifications_enabled"],
        "theme": ob["theme"],
        "theme_options": THEME_OPTIONS,
        "dark_mode": ob["dark_mode"],
        "colorblind_mode": ob["colorblind_mode"],
        "colorblind_options": COLORBLIND_OPTIONS,
    }
