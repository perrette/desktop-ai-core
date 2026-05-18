import logging
from typing import Callable

_default_logger = logging.getLogger("desktop_ai_core")


class AbstractFrontendApp:
    """Generic frontend application scaffolding.

    Holds the lifecycle pieces that are shared across desktop AI apps:
    a ``view`` reference, a parameter dict, a logger, and an
    ``error_callback`` hook surfaced through :meth:`notify_error`.
    Audio, clipboard, and chunk-rendering concerns belong to subclasses.
    """

    def __init__(
        self,
        params=None,
        view=None,
        logger=_default_logger,
        error_callback: Callable[[str, str], None] | None = None,
    ):
        self.params = params or {}
        self.view = view
        self.logger = logger
        self.error_callback = error_callback

    def notify_error(self, title: str, message: str) -> None:
        self.logger.error(f"{title}: {message}")
        if self.error_callback is not None:
            try:
                self.error_callback(title, message)
            except Exception as cb_exc:
                self.logger.error(f"error_callback raised: {cb_exc}")

    def set_param(self, item, value=None):
        self.params[str(item)] = item.value if hasattr(item, "value") and value is None else value

    def get_param(self, item):
        return self.params.get(str(item))

    def checked(self, item):
        return self.get_param(str(item))

    def callback_toggle_option(self, view, item):
        self.set_param(str(item), not self.get_param(str(item)))

    def set_audioplayer(self, view, player):
        """Protocol hook for subclasses that own an audio player.

        Subclasses with audio concerns override this to wire the player
        to the view. The base implementation is a no-op so generic
        callers can invoke it unconditionally.
        """
        return None
