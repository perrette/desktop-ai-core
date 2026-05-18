import time as _time


_FLAGS = {
    "en-US": "🇺🇸",
    "en-GB": "🇬🇧",
    "fr-FR": "🇫🇷",
    "de-DE": "🇩🇪",
    "es-ES": "🇪🇸",
    "it-IT": "🇮🇹",
    "ja-JP": "🇯🇵",
    "zh-CN": "🇨🇳",
}


def flag_for(language: str | None) -> str:
    if language is None:
        return ""
    return _FLAGS.get(language, "")


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
