#!/usr/bin/env python3
"""
Run comprehensive tool tests with ALL output logged to a timestamped file.
Usage: python tests/run_tests_with_logging.py
       python tests/run_tests_with_logging.py -v  # verbose
       python tests/run_tests_with_logging.py -k web_search  # filter tests
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import pytest  # noqa: E402

# Setup logging BEFORE any other imports (must run before pytest)
from tests.test_logging import get_log_path, setup_test_logging  # noqa: E402

log_path = setup_test_logging()
print(f"\n{'='*60}")
print(f"All output logged to: {log_path}")
print(f"{'='*60}\n")

if __name__ == "__main__":
    args = sys.argv[1:] if len(sys.argv) > 1 else ["-v", "-s", "--tb=short"]
    exit_code = pytest.main(args)
    print(f"\n>>> Log file: {get_log_path()}\n")
    sys.exit(exit_code)
