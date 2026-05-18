def format_openai_error(exc):
    """Turn an openai exception into a (title, message) tuple suited for a user dialog."""
    import openai
    body = getattr(exc, "body", None) or {}
    err = body.get("error") if isinstance(body, dict) else None
    code = (err or {}).get("code") if isinstance(err, dict) else None
    api_message = (err or {}).get("message") if isinstance(err, dict) else None
    detail = api_message or str(exc) or exc.__class__.__name__

    if isinstance(exc, openai.AuthenticationError):
        return "Authentication failed", f"Check your API key.\n\n{detail}"
    if isinstance(exc, openai.PermissionDeniedError):
        return "Permission denied", detail
    if isinstance(exc, openai.RateLimitError):
        if code == "insufficient_quota" or "quota" in detail.lower() or "credit" in detail.lower():
            return ("Credits exhausted",
                    f"Your account is out of credits or has hit its quota.\n\n{detail}")
        return "Rate limit", detail
    if isinstance(exc, openai.APIConnectionError):
        return "Connection error", f"Could not reach the API.\n\n{detail}"
    if isinstance(exc, openai.BadRequestError):
        return "Bad request", detail
    return f"API error ({exc.__class__.__name__})", detail
