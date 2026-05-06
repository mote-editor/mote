from pathlib import Path


def save_buffer(buffer, path=None):
    """Save a buffer to disk.

    Returns True on success, False if there is no path or write fails.
    """
    target = path or getattr(buffer, "file_path", None) or buffer.name
    if not target or target == "Untitled":
        return False

    try:
        file_path = Path(target)
        file_path.write_text(buffer.get_full_text(), encoding="utf-8")
    except OSError:
        return False

    buffer.dirty = False
    buffer.name = str(file_path)
    return True
