"""Database initialization script."""
from pathlib import Path


def main() -> None:
    db_path = Path("database/nifty100.db")
    db_path.touch(exist_ok=True)
    print(f"Database ready at {db_path}")


if __name__ == "__main__":
    main()
