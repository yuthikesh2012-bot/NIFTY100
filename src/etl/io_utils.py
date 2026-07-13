from pathlib import Path
def ensure_exists(path):
    p=Path(path)
    if not p.exists():
        raise FileNotFoundError(path)
    return p
