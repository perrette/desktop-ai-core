import time as _time
import os as _os
import tempfile as _tempfile
import sys as _sys
import signal as _signal
import logging as _logging
from pathlib import Path


_COUNTRY_FLAGS = {
    "US": "🇺🇸",
    "GB": "🇬🇧",
    "FR": "🇫🇷",
    "DE": "🇩🇪",
    "ES": "🇪🇸",
    "IT": "🇮🇹",
    "JP": "🇯🇵",
    "CN": "🇨🇳",
    "IN": "🇮🇳",
    "BR": "🇧🇷",
    "PT": "🇵🇹",
}

# Short ISO 639-1 → country of origin. The European convention (politically
# neutral, language-as-cultural-artefact) maps each language to where it
# was born rather than where it has the most speakers today: English →
# Britain, Spanish → Spain, Portuguese → Portugal. Callers that want a
# specific regional variant (en-US, pt-BR) should pass the long BCP-47
# tag — `default_country` extracts the region from it directly.
_LANG_DEFAULT_COUNTRY = {
    "en": "GB",
    "fr": "FR",
    "de": "DE",
    "es": "ES",
    "it": "IT",
    "ja": "JP",
    "zh": "CN",
    "hi": "IN",
    "pt": "PT",
}


def default_country(language: str | None) -> str | None:
    """Return the ISO 3166-1 alpha-2 country code to use as the default
    flag for a language tag.

    Long BCP-47 tags ('en-US', 'pt-BR') extract their explicit region.
    Short ISO 639-1 codes ('en', 'fr') resolve to the language's country
    of origin ('en' → 'GB', 'es' → 'ES', 'pt' → 'PT'). Returns None
    when the language is unknown so callers can choose their fallback.
    """
    if language is None:
        return None
    if "-" in language:
        return language.split("-", 1)[1]
    return _LANG_DEFAULT_COUNTRY.get(language)


def flag_for(language: str | None) -> str:
    """Return the flag emoji for a language tag, or empty string when
    no mapping is known. See `default_country` for the lookup rules.

    Treats None and "" from `default_country` identically (both mean
    'no country mapping'), so callers can disable flags entirely by
    clearing `_LANG_DEFAULT_COUNTRY` — every lookup falls through to
    "" without needing to also touch this function."""
    country = default_country(language)
    if not country:
        return ""
    return _COUNTRY_FLAGS.get(country, "")


def _pidfile_path(name: str) -> Path:
    """Return the PID file path for *name* in a portable runtime directory.

    On Linux, honour ``XDG_RUNTIME_DIR`` (a per-user, tmpfs-backed dir) when
    set, falling back to the system temp dir. On Windows and macOS there is no
    ``XDG_RUNTIME_DIR`` and no ``/tmp``, so use ``tempfile.gettempdir()`` which
    resolves to the correct per-user/system temp folder on every platform
    (``/tmp`` on Linux, ``%TEMP%`` on Windows, ``$TMPDIR`` on macOS). This keeps
    write/read/delete in sync via a single source of truth."""
    runtime_dir = _os.environ.get("XDG_RUNTIME_DIR") or _tempfile.gettempdir()
    return Path(runtime_dir) / f"{name}.pid"


def write_pidfile(name: str) -> Path:
    """Write a PID file for the named application. Returns the file path."""
    pid_path = _pidfile_path(name)
    with open(pid_path, "w") as f:
        f.write(str(_os.getpid()))
    # 0o600 is a POSIX permission concept; chmod is a no-op for the mode bits on
    # Windows and can raise on some filesystems, so only apply it off-Windows.
    if _sys.platform != "win32":
        try:
            pid_path.chmod(0o600)
        except OSError:
            pass
    return pid_path


def remove_pidfile(name: str) -> None:
    """Remove the PID file for the named application. Silently ignores missing files."""
    pid_path = _pidfile_path(name)
    try:
        pid_path.unlink()
    except FileNotFoundError:
        pass


def register_signal_toggle(signal_number: int, callback) -> None:
    """Register *callback* as the handler for *signal_number*.

    On platforms where the signal is unavailable the call is a no-op logged at
    DEBUG level instead of raising.
    """
    try:
        _signal.signal(signal_number, lambda *_: callback())
    except (OSError, ValueError) as exc:
        _logging.debug("register_signal_toggle: signal %d not available: %s", signal_number, exc)


_UNSET = object()


class MultiStateTrayIcon:
    """Drive state-based image swaps on a pystray-style tray icon.

    The helper wraps an existing icon and a mapping of state-name -> PIL
    image. A caller-supplied ``get_state`` callable is queried on each
    ``update`` to derive the current logical state (e.g. ``"recording"``,
    ``"busy"``, or ``None`` for idle); when the value differs from the
    previously applied state, the icon's image is swapped and
    ``icon.update_menu()`` is called so visibility predicates re-evaluate.

    A ``start_monitoring`` helper runs a poll loop (intended to be invoked
    from a background thread) that keeps calling ``update`` while a
    ``should_continue`` callable returns truthy, then performs one final
    update before exiting so the icon settles to whatever the current state
    is when the loop ends.

    Parameters
    ----------
    icon:
        A pystray ``Icon``-compatible object exposing assignable ``.icon``
        and a callable ``.update_menu()``.
    images:
        Mapping of state name -> ``PIL.Image``. Use ``None`` as the key for
        the idle state. Every value that ``get_state`` can return must be a
        key.
    get_state:
        Zero-argument callable returning the current state name (or
        ``None``).
    poll_interval:
        Seconds between polls in ``start_monitoring``. Defaults to 0.1.
    """

    def __init__(self, icon, images, get_state, poll_interval=0.1):
        self.icon = icon
        self.images = images
        self.get_state = get_state
        self.poll_interval = poll_interval
        self._current = _UNSET

    def update(self, force=False):
        state = self.get_state()
        if not force and state == self._current:
            return
        self.icon.icon = self.images[state]
        self._current = state
        self.icon.update_menu()

    def start_monitoring(self, should_continue):
        try:
            while should_continue():
                self.update()
                _time.sleep(self.poll_interval)
        finally:
            self.update()
