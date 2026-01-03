API_LIMITS = {
    "free": 2,
    "pro": 12,
    "plus": 10000,
}

DOWNLOAD_LIMITS = {
    "free": 1,
    "pro": 999999,
    "plus": 999999,
}

LLM_LIMITS = {
    "free": 1,
    "pro": 999999,
    "plus": 999999,
}


def check_api_usage(db, user):
    """
    Decrement user's remaining API calls.
    Returns True if allowed, False if limit reached.
    """
    if user.api_calls <= 0:
        return False

    user.api_calls -= 1
    db.commit()
    return True


def check_download_usage(db, user):
    """
    Decrement user's remaining downloads.
    Returns True if allowed, False if limit reached.
    """
    if user.api_downloads <= 0:
        return False

    user.api_downloads -= 1
    db.commit()
    return True


def check_llm_usage(db, user):
    """
    Decrement user's remaining LLM runs.
    Returns True if allowed, False if limit reached.
    """
    if user.llm_runs <= 0:
        return False

    user.llm_runs -= 1
    db.commit()
    return True
