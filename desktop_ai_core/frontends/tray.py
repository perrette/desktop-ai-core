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
