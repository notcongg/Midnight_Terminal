from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path

from prompt_toolkit.auto_suggest import AutoSuggest, Suggestion
from prompt_toolkit.completion import Completer, Completion

from src.cmd.rootfs.env.env import ENV
from src.cmd.utils.registry import COMMANDS


# ============================================================
# Filesystem path completion and suggestion helpers
# ============================================================


def _resolve_path_relative_to_cwd(
    value: str,
    cwd: str,
) -> Path:
    """Resolve a user-typed path fragment relative to cwd.

    Handles:
    - ``src/``              -> ``cwd/src/``
    - ``src/cmd/``          -> ``cwd/src/cmd/``
    - ``~/.mid``            -> ``HOME/.mid``
    - ``/absolute/path``    -> ``/absolute/path``
    - ``plain_name``        -> ``cwd/plain_name``
    """
    if value.startswith("~"):
        return Path(value).expanduser()

    candidate = Path(value)

    if candidate.is_absolute():
        return candidate

    return Path(cwd) / value


def _split_dir_and_trailing(
    value: str,
    cwd: str,
) -> tuple[Path, str]:
    """Split ``value`` into ``(parent_directory, trailing_name)``.

    Examples:
        ``src/cmd/``    -> ``(cwd/src/cmd, "")``
        ``src/cmd/abc`` -> ``(cwd/src/cmd, "abc")``
        ``src/``        -> ``(cwd/src, "")``
        ``src``         -> ``(cwd, "src")``
        ``~/.mid``      -> ``(HOME, ".mid")``
        ``/abs/x``      -> ``(/abs, "x")``
    """
    ends_with_sep = value.endswith("/") or value.endswith("\\")

    if value.startswith("~"):
        expanded = Path(value).expanduser()
    else:
        expanded = Path(value)

    if ends_with_sep:
        clean = value.rstrip("/\\")
        if not clean:
            parent = Path.home() if value.startswith("~") else Path("/")
        elif clean.startswith("~"):
            parent = Path(clean).expanduser()
        elif Path(clean).is_absolute():
            parent = Path(clean)
        else:
            parent = Path(clean)
        trailing = ""
    elif expanded.is_absolute():
        parts = expanded.parts
        if len(parts) > 1:
            parent = Path(*parts[:-1])
            trailing = parts[-1]
        else:
            parent = expanded.parent
            trailing = expanded.name
    elif "/" in value or "\\" in value:
        parent = expanded.parent
        trailing = expanded.name
    else:
        parent = Path(cwd)
        trailing = value

    return parent, trailing


class PathCompletionProvider:
    """File/path completion and suggestion for a single typed fragment.

    Produces completions relative to the current working directory so
    that ``cat src/`` lists entries inside ``cwd/src/`` rather than
    searching for a basename ``src`` anywhere.
    """

    def __init__(self, cwd: str) -> None:
        self._cwd = cwd

    def candidates_for(
        self,
        fragment: str,
    ) -> tuple[str | None, list[Completion]]:
        """Return ``(suffix_to_replace, completions)``.

        *suffix_to_replace* is the portion of *fragment* that should be
        replaced by the chosen completion (used by the completer's
        ``start_position``).  It is ``None`` when there is no clear
        single match to inject.
        """
        if not fragment:
            return None, []

        parent_dir, trailing = _split_dir_and_trailing(fragment)

        try:
            resolved_parent = _resolve_path_relative_to_cwd(
                str(parent_dir),
                self._cwd,
            )
        except (OSError, ValueError):
            return None, []

        if not resolved_parent.is_dir():
            return None, []

        try:
            entries = sorted(resolved_parent.iterdir())
        except OSError:
            return None, []

        matches = [
            entry for entry in entries
            if entry.name.startswith(trailing)
        ]

        if not matches:
            return None, []

        completions: list[Completion] = []
        for entry in matches[:50]:
            completion_text = str(resolved_parent / entry.name)

            try:
                completion_text = str(
                    Path(completion_text).relative_to(Path(self._cwd))
                )
            except ValueError:
                pass

            completions.append(
                Completion(
                    text=completion_text,
                    start_position=-len(trailing),
                    display_meta="dir" if entry.is_dir() else "file",
                )
            )

        if len(matches) == 1:
            return trailing, completions

        return None, completions

    def suggestion_for(self, fragment: str) -> Suggestion | None:
        """Return a gray inline suggestion for *fragment*, if unambiguous."""
        if not fragment:
            return None

        parent_dir, trailing = _split_dir_and_trailing(fragment)

        try:
            resolved_parent = _resolve_path_relative_to_cwd(
                str(parent_dir),
                self._cwd,
            )
        except (OSError, ValueError):
            return None

        if not resolved_parent.is_dir():
            return None

        try:
            entries = sorted(resolved_parent.iterdir())
        except OSError:
            return None

        matches = [
            entry for entry in entries
            if entry.name.startswith(trailing)
        ]

        if len(matches) == 1:
            return Suggestion(matches[0].name[len(trailing):])

        return None


class PathAutoSuggest(AutoSuggest):
    """Gray inline suggestion for filesystem paths based on cwd.

    Mirrors the active completion candidates but only surfaces the single
    best match as a gray suffix, exactly like AutoSuggestFromHistory does
    for history.  This is separate from history suggestions so that a typed
    path like ``cat src/`` gets a gray ``lib/`` hint from the actual
    filesystem instead of a random history entry.
    """

    def __init__(self, cwd: str) -> None:
        self._cwd = cwd
        self._provider = PathCompletionProvider(cwd)

    def get_suggestion(self, buffer, document):
        text = document.text

        if " " in text or "\t" in text:
            fragment = text.rsplit(" ", 1)[-1]

            if "\t" in fragment:
                fragment = fragment.rsplit("\t", 1)[-1]
        else:
            fragment = text

        if not fragment:
            return None

        return self._provider.suggestion_for(fragment)


class MidnightCompleter(Completer):
    def __init__(self, cwd: str = ".") -> None:
        self._cwd = cwd

    def get_completions(
        self,
        document,
        complete_event,
    ) -> Iterable[Completion]:

        if ENV.get(
            "INPUT.AUTOCOMPLETE",
            "true",
        ).lower() != "true":
            return

        text = document.text_before_cursor

        # Chỉ autocomplete command đầu tiên.
        if " " in text or "\t" in text:
            yield from _path_candidates(text, self._cwd)
            return

        current = text.lower()

        if not current:
            return

        for command in COMMANDS:
            if command.lower().startswith(current):
                yield Completion(
                    command,
                    start_position=-len(text),
                )


def _path_candidates(fragment: str, cwd: str) -> Iterable[Completion]:
    """File/path completion candidates for the token currently being typed.

    Kept for backwards-compatibility; new code should use
    ``PathCompletionProvider.candidates_for`` directly.
    """
    parts = fragment.replace("\t", " ").split(" ")
    path_fragment = parts[-1]

    provider = PathCompletionProvider(cwd)
    _, completions = provider.candidates_for(path_fragment)
    yield from completions
