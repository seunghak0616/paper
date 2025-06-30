#!/usr/bin/env python3
"""
Test runner script with coverage reporting.
"""

import os
import subprocess
import sys
from pathlib import Path


def run_command(command, description):
    """Run a command and handle errors."""
    print(f"\n🔧 {description}")
    print(f"Running: {' '.join(command)}")

    result = subprocess.run(command, capture_output=True, text=True)

    if result.returncode == 0:
        print("✅ Success")
        if result.stdout:
            print(result.stdout)
    else:
        print("❌ Failed")
        if result.stderr:
            print(result.stderr)
        if result.stdout:
            print(result.stdout)
        return False

    return True


def main():
    """Main test runner."""
    print("🧪 Papers API Test Suite")
    print("=" * 50)

    # Check if we're in the right directory
    if not Path("app").exists():
        print("❌ Please run this script from the project root directory")
        sys.exit(1)

    # Set environment for testing
    os.environ["ENVIRONMENT"] = "testing"
    os.environ["OPENAI_API_KEY"] = "sk-test-key-for-testing-only"

    # Test commands to run
    test_commands = [
        {
            "cmd": ["python", "-m", "pytest", "--version"],
            "desc": "Checking pytest installation"
        },
        {
            "cmd": ["python", "-m", "pytest", "tests/unit/", "-v", "--tb=short"],
            "desc": "Running unit tests"
        },
        {
            "cmd": ["python", "-m", "pytest", "tests/integration/", "-v", "--tb=short"],
            "desc": "Running integration tests"
        },
        {
            "cmd": ["python", "-m", "pytest", "--cov=app", "--cov-report=term-missing", "--cov-report=html"],
            "desc": "Running all tests with coverage"
        },
        {
            "cmd": ["python", "-m", "pytest", "-m", "not slow", "--cov=app", "--cov-fail-under=50"],
            "desc": "Running fast tests with minimum coverage check"
        }
    ]

    failed_commands = []

    for test_cmd in test_commands:
        if not run_command(test_cmd["cmd"], test_cmd["desc"]):
            failed_commands.append(test_cmd["desc"])

    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Summary")
    print("=" * 50)

    if failed_commands:
        print("❌ Some tests failed:")
        for cmd in failed_commands:
            print(f"  - {cmd}")
        print("\n📄 Check the detailed output above for more information.")
        sys.exit(1)
    else:
        print("✅ All tests passed!")

        # Coverage report location
        if Path("htmlcov/index.html").exists():
            print(f"📈 Coverage report: {Path('htmlcov/index.html').absolute()}")

        print("\n🎉 Test suite completed successfully!")


if __name__ == "__main__":
    main()
