"""Small shared helpers."""


def coalesce(*values):
    """Return the first value that is not None."""
    for value in values:
        if value is not None:
            return value
    return None
