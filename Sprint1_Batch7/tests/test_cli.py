from src.features.cli import main

def test_cli_import():
    assert callable(main)
