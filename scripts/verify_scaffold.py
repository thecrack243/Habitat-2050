"""Run portable scaffold checks without installing third-party packages."""

from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]


def main(pattern: str = "test_scaffold.py") -> int:
    sys.dont_write_bytecode = True
    sys.path.insert(0, str(ROOT / "src"))
    suite = unittest.defaultTestLoader.discover(
        start_dir=str(ROOT / "tests"), pattern=pattern
    )
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    return 0 if result.wasSuccessful() and result.testsRun > 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
