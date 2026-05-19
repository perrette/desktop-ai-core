# desktop-ai-core

Shared provider abstractions and frontend scaffolding for desktop AI applications.

This package supplies the common primitives consumed by
[Bard](https://github.com/perrette/bard) (TTS) and
[Scribe](https://github.com/perrette/scribe) (STT) so each app can focus on its
domain-specific logic rather than re-implementing the shared shell. It is
intentionally small, dependency-free at the core, and designed to be pulled in
as a git dependency.

## What's in the box

- `desktop_ai_core.providers` — `Backend` / `TTSBackend` / `STTBackend`
  abstract bases, `Voice` and `LanguageModel` dataclasses, a tiny
  register/probe/get registry shared between apps, and a `format_openai_error`
  helper for turning `openai` SDK exceptions into user-facing `(title, message)`
  tuples.
- `desktop_ai_core.frontends` — `AbstractFrontendApp` lifecycle base, a
  terminal menu mini-framework (`Menu`, `Item`, `SetValueItem`), a
  `MultiStateTrayIcon` driver for pystray-style icons (plus `flag_for`,
  PID-file helpers, and a `register_signal_toggle` shim), and a
  thread-safe `show_error_dialog` built on Tk.
- `desktop_ai_core.install` — `install_desktop_file`, an XDG `.desktop` entry
  writer for Linux desktop integration.

## Installation

```bash
pip install desktop-ai-core
```

Or pin from a consumer project's `pyproject.toml`:

```toml
[project]
dependencies = [
    "desktop-ai-core>=0.1",
]
```

If you need an unreleased commit, you can also pull it straight from git:

```toml
"desktop-ai-core @ git+https://github.com/perrette/desktop-ai-core.git@<sha>",
```

For local development against a checkout, use an editable install:

```bash
pip install -e /path/to/desktop-ai-core
```

Requires Python 3.9+. The core has **no runtime dependencies**; optional
features pull their dependencies from the consumer (e.g. `openai` for
`format_openai_error`, `pystray` + `PIL` for `MultiStateTrayIcon`, `tkinter`
for `show_error_dialog`).

## Providers

### Backend types

`TTSBackend` and `STTBackend` are abstract base classes that consumer code
subclasses to wrap a concrete service (OpenAI, ElevenLabs, faster-whisper,
Groq, …). They expose a small, stable surface:

```python
from pathlib import Path
from desktop_ai_core.providers import TTSBackend, STTBackend, Voice

class MyTTS(TTSBackend):
    name = "mytts"
    default_voice = "alloy"
    default_model = "tts-1"
    output_format = "mp3"
    sample_rate = 24_000
    supports_streaming = False

    def synthesize(self, text: str, out_path: Path) -> Path: ...
    def list_voices(self) -> list[str]: ...
    # optional: list_voices_meta() -> list[Voice], list_models(), synthesize_stream(text)

class MySTT(STTBackend):
    name = "mystt"
    default_model = "whisper-1"

    def transcribe(self, audio_path: Path) -> str: ...
```

Class-level `is_local: bool` and `install_hint: str | None` let consumers
group local vs. cloud backends in menus and surface install instructions when
a backend is missing.

`Voice` and `LanguageModel` are frozen dataclasses that backends can return
from their listing methods to give the UI richer metadata than bare ids.

### Registry

A pair of process-global registries — one for TTS, one for STT — let apps
discover backends without hard-wiring imports:

```python
from desktop_ai_core.providers import (
    register_tts, get_tts, available_tts, probe_tts,
    register_stt, get_stt, available_stt, probe_stt,
)

def _probe() -> tuple[bool, str | None]:
    try:
        import openai  # noqa
        return True, None
    except ImportError:
        return False, "pip install openai"

register_tts("openai", MyTTS, probe=_probe)

backend = get_tts("openai", api_key=...)        # instantiates with kwargs
names    = available_tts()                       # ["openai", ...]
ok, hint = probe_tts("openai")                   # availability check
```

The `probe` callable is optional; backends without one are assumed available.
Registration is typically done at import time inside each backend's module.

### Error formatting

`format_openai_error(exc)` maps an `openai.*Error` to a `(title, message)`
tuple suited for `show_error_dialog`. It distinguishes
`AuthenticationError`, `PermissionDeniedError`, `RateLimitError` (with a
dedicated "Credits exhausted" branch for `insufficient_quota`),
`APIConnectionError`, and `BadRequestError`, falling back to a generic
`API error (<ClassName>)` for everything else.

## Frontends

### `AbstractFrontendApp`

A minimal lifecycle base that holds a `params` dict, a `view` reference, a
`logger`, and an `error_callback`. Helpers cover the common menu-driven
patterns: `set_param` / `get_param` / `checked` / `callback_toggle_option`,
plus `notify_error(title, message)` which logs the error and fans out to the
callback (wrapped in try/except so a broken UI never takes the app down).
`set_audioplayer` is a no-op hook subclasses with audio concerns override.

### Terminal menu

A small text-mode menu framework that mirrors the structure of a tray-icon
menu so the same `Item` graph can drive both:

- `Item(name, callback, checked=None, checkable=False, visible=True, help="")`
  — leaf action; `checked` and `visible` may be callables for live state.
- `SetValueItem(name, callback, value=None, choices=None, type=None, ...)`
  — prompts for input, validates against `type` / `choices`, then invokes
  the callback.
- `Menu(items, name=None, help="")` — renders a numbered list and loops
  until the user enters `q`/`quit` or an item callback returns `False`.

### Tray helpers

- `MultiStateTrayIcon(icon, images, get_state, poll_interval=0.1)` — wraps
  a pystray-compatible icon and a `{state_name: PIL.Image}` map; call
  `update()` (or `start_monitoring(should_continue)` from a background
  thread) and the icon swaps images whenever `get_state()` returns a new
  value, then calls `icon.update_menu()` so visibility predicates
  re-evaluate. Use `None` as the dict key for the idle state.
- `flag_for(language)` — emoji flag for a BCP-47 language tag (en-US,
  fr-FR, …), empty string for unknown.
- `write_pidfile(name)` / `remove_pidfile(name)` — write/remove
  `$XDG_RUNTIME_DIR/<name>.pid` (falling back to `/tmp`), with `0o600`
  permissions. `remove_pidfile` silently ignores a missing file.
- `register_signal_toggle(signal_number, callback)` — install a signal
  handler that invokes `callback()`, degrading to a DEBUG log on platforms
  where the signal is unavailable (instead of raising).

### Error dialog

`show_error_dialog(title, message)` pops a modal Tk `messagebox.showerror`
from a fresh daemon thread, so it is safe to call from anywhere — including
while a pystray/GTK main loop owns the main thread. If Tk is unavailable
the call falls back to a stderr-style print rather than raising.

## Desktop integration

`install_desktop_file(template, name, icon_folder, bin_folder, terminal,
startup_wm_class, options="")` renders a `.desktop` entry template and
writes it to `$XDG_DATA_HOME/applications/` (default
`~/.local/share/applications/`). The template is a normal `str.format`
string with placeholders `{icon_folder}`, `{bin_folder}`, `{name}`,
`{terminal}`, `{StartupWMClass}`, and `{options}`. The function raises
`NotImplementedError` on non-Linux platforms — macOS/Windows packaging is
out of scope for now.

## Consumer projects

- **Scribe** — desktop speech-to-text. Registers STT backends
  (faster-whisper, Groq, OpenAI) against `register_stt` and subclasses
  `AbstractFrontendApp` for the tray app.
- **Bard** — desktop text-to-speech. Registers TTS backends against
  `register_tts`; same frontend scaffolding.

Both projects depend on `desktop-ai-core` and treat its public surface
(everything re-exported from `desktop_ai_core.providers.__init__` and
`desktop_ai_core.frontends.__init__`) as the stable contract.

## Design notes

- **Zero runtime deps in the core.** Optional features (openai error
  formatting, pystray icons, Tk dialogs) import their dependencies lazily
  so a consumer that does not use them does not pay for them.
- **Registry over plugins.** Backends self-register at import time; the
  registry is just a `dict`, with optional `probe` callables so the UI can
  show install hints instead of crashing on missing extras.
- **Frontend-agnostic state.** `AbstractFrontendApp` holds parameters and
  a view reference but knows nothing about pystray, Tk, or the terminal —
  the same app object drives tray and terminal frontends.
- **Linux first.** Desktop-file installation and PID/signal helpers target
  Linux; structures that could in principle work elsewhere
  (`MultiStateTrayIcon`, `show_error_dialog`) do, but are not actively
  exercised on macOS/Windows.

## License

MIT — see [LICENSE](LICENSE).
