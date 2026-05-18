from typing import Callable

from desktop_ai_core.providers.base import STTBackend, TTSBackend


_TTS_REGISTRY: dict[str, type[TTSBackend]] = {}
_TTS_PROBES: dict[str, Callable[[], tuple[bool, str | None]]] = {}


def register_tts(
    name: str,
    backend_cls: type[TTSBackend],
    *,
    probe: Callable[[], tuple[bool, str | None]] | None = None,
) -> type[TTSBackend]:
    _TTS_REGISTRY[name] = backend_cls
    if probe is not None:
        _TTS_PROBES[name] = probe
    return backend_cls


def get_tts(name: str, **kwargs) -> TTSBackend:
    if name not in _TTS_REGISTRY:
        raise KeyError(name)
    return _TTS_REGISTRY[name](**kwargs)


def available_tts() -> list[str]:
    return list(_TTS_REGISTRY)


def probe_tts(name: str) -> tuple[bool, str | None]:
    if name not in _TTS_REGISTRY:
        raise KeyError(name)
    if name in _TTS_PROBES:
        return _TTS_PROBES[name]()
    return True, None


_STT_REGISTRY: dict[str, type[STTBackend]] = {}
_STT_PROBES: dict[str, Callable[[], tuple[bool, str | None]]] = {}


def register_stt(
    name: str,
    backend_cls: type[STTBackend],
    *,
    probe: Callable[[], tuple[bool, str | None]] | None = None,
) -> type[STTBackend]:
    _STT_REGISTRY[name] = backend_cls
    if probe is not None:
        _STT_PROBES[name] = probe
    return backend_cls


def get_stt(name: str, **kwargs) -> STTBackend:
    if name not in _STT_REGISTRY:
        raise KeyError(name)
    return _STT_REGISTRY[name](**kwargs)


def available_stt() -> list[str]:
    return list(_STT_REGISTRY)


def probe_stt(name: str) -> tuple[bool, str | None]:
    if name not in _STT_REGISTRY:
        raise KeyError(name)
    if name in _STT_PROBES:
        return _STT_PROBES[name]()
    return True, None
