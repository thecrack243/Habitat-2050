"""Run scaffold, scientific pipeline, and Streamlit application checks."""

from verify_scaffold import main


if __name__ == "__main__":
    raise SystemExit(main("test_*.py"))
