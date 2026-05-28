def is_valid_session(session_id: str) -> bool:
    return bool(session_id and len(session_id) > 10)