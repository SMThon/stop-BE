import uuid


def new_id() -> str:
    """기존 backend/(Node)와 같은 UUID 문자열 ID."""
    return str(uuid.uuid4())
