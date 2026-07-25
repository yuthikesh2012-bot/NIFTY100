"""Reset local database state."""
from pathlib import Path


def main() -> None:
    db_path = Path("database/nifty100.db")
    if db_path.exists():
        db_path.unlink()
    db_path.touch(exist_ok=True)
    print(f"Reset database at {db_path}")


if __name__ == "__main__":
    main()
