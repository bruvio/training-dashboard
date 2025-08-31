#!/usr/bin/env python3
"""
Test runner script for Garmin Dashboard.

Runs comprehensive test suite and reports results for validation gates
following the enhanced PRP specification.
"""

from pathlib import Path
import subprocess
import sys
from typing import Dict, List, Tuple


def run_command(cmd: List[str], description: str) -> Tuple[bool, str]:
    """
    Run a command and return success status and output.

    Args:
        cmd: Command to run as list of strings
        description: Description of what the command does

    Returns:
        Tuple of (success, output)
    """
    print(f"🔄 {description}...")

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=False, cwd=Path(__file__).parent)

        if result.returncode == 0:
            print(f"✅ {description} - PASSED")
            return True, result.stdout
        else:
            print(f"❌ {description} - FAILED")
            print(f"Error output: {result.stderr}")
            return False, result.stderr

    except Exception as e:
        print(f"❌ {description} - ERROR: {e}")
        return False, str(e)


def run_test_suite() -> Dict[str, bool]:
    """
    Run comprehensive test suite with different categories.

    Returns:
        Dictionary mapping test category to success status
    """
    print("🏃 Starting Garmin Dashboard Test Suite")
    print("=" * 60)

    # 1. Unit tests for models
    success, output = run_command(
        ["python", "-m", "pytest", "tests/test_models.py", "-v", "--tb=short"], "Running SQLAlchemy model tests"
    )
    results = {"models": success}
    # 2. Unit tests for parsers
    success, output = run_command(
        ["python", "-m", "pytest", "tests/test_parser.py", "-v", "--tb=short"], "Running file parser tests"
    )
    results["parsers"] = success

    # 3. Integration tests for web queries
    success, output = run_command(
        ["python", "-m", "pytest", "tests/test_web_queries.py", "-v", "--tb=short"],
        "Running web query integration tests",
    )
    results["web_queries"] = success

    # 4. Full test suite with coverage
    success, output = run_command(
        [
            "python",
            "-m",
            "pytest",
            "tests/",
            "-v",
            "--tb=short",
            "--cov=app",
            "--cov=ingest",
            "--cov-report=term-missing",
        ],
        "Running full test suite with coverage",
    )
    results["full_suite"] = success

    return results


def check_code_quality() -> Dict[str, bool]:
    """
    Run code quality checks.

    Returns:
        Dictionary mapping quality check to success status
    """
    print("\n🔍 Running Code Quality Checks")
    print("=" * 60)

    # 1. Black code formatting check
    success, output = run_command(
        ["python", "-m", "black", "--check", "--diff", "app/", "ingest/", "cli/", "tests/"],
        "Checking code formatting with Black",
    )
    results = {"black": success}
    # 2. isort import sorting check
    success, output = run_command(
        ["python", "-m", "isort", "--check-only", "--diff", "app/", "ingest/", "cli/", "tests/"],
        "Checking import sorting with isort",
    )
    results["isort"] = success

    return results


def validate_project_structure() -> bool:
    """
    Validate that all required files and directories exist.

    Returns:
        True if project structure is valid
    """
    print("\n📁 Validating Project Structure")
    print("=" * 60)

    required_files = [
        "app/__init__.py",
        "app/dash_app.py",
        "app/data/models.py",
        "app/data/db.py",
        "app/data/web_queries.py",
        "app/data/queries.py",
        "app/pages/calendar.py",
        "app/pages/activity_detail.py",
        "ingest/__init__.py",
        "ingest/parser.py",
        "cli/__init__.py",
        "cli/gd_import.py",
        "tests/test_models.py",
        "tests/test_parser.py",
        "tests/test_web_queries.py",
        "tests/conftest.py",
        "requirements.txt",
    ]

    if missing_files := [file_path for file_path in required_files if not Path(file_path).exists()]:
        print("❌ Missing required files:")
        for file_path in missing_files:
            print(f"   - {file_path}")
        return False
    else:
        print("✅ All required files present")
        return True


def main():
    """Main test runner function."""
    print("🏃 Garmin Dashboard - Test Suite Runner")
    print("Research-validated testing following enhanced PRP specifications")
    print("=" * 80)

    # Track overall success
    all_passed = True

    # 1. Validate project structure
    structure_valid = validate_project_structure()
    if not structure_valid:
        print("\n❌ Project structure validation failed")
        all_passed = False

    # 2. Run test suite
    test_results = run_test_suite()
    test_success = all(test_results.values())

    if not test_success:
        print("\n❌ Some tests failed:")
        for category, passed in test_results.items():
            status = "✅ PASSED" if passed else "❌ FAILED"
            print(f"   {category}: {status}")
        all_passed = False

    # 3. Run code quality checks (optional - don't fail on these)
    quality_results = check_code_quality()
    quality_success = all(quality_results.values())

    if not quality_success:
        print("\n⚠️  Code quality checks have issues (won't fail build):")
        for check, passed in quality_results.items():
            status = "✅ PASSED" if passed else "⚠️  ISSUES"
            print(f"   {check}: {status}")

    # Final summary
    print("\n" + "=" * 80)
    print("📊 FINAL RESULTS")
    print("=" * 80)

    if all_passed:
        print("🎉 ALL VALIDATION GATES PASSED!")
        print("✅ Project structure: Valid")
        print("✅ Test suite: All tests passing")
        print("📦 Ready for deployment")

        # Additional success information
        print("\n📈 Test Categories Passed:")
        for category, passed in test_results.items():
            if passed:
                print(f"   ✅ {category}")

        return 0
    else:
        print("❌ VALIDATION FAILED - Some checks did not pass")
        print("\n🔧 Required fixes:")

        if not structure_valid:
            print("   - Fix project structure issues")

        for category, passed in test_results.items():
            if not passed:
                print(f"   - Fix failing tests in: {category}")

        return 1


if __name__ == "__main__":
    sys.exit(main())
