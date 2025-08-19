"""
Test suite for the Modular Chatbot application.

This module provides utilities for running different types of tests:
- Unit tests: Fast, isolated tests with mocked dependencies
- Integration tests: Tests that interact with test database
- E2E tests: Full-stack tests with real services (marked as slow)

Usage:
    # Run all unit and integration tests
    python -m backend.tests
    
    # Run only unit tests
    python -m backend.tests --unit-only
    
    # Run only integration tests  
    python -m backend.tests --integration-only
    
    # Run unit and integration tests (exclude E2E)
    python -m backend.tests --no-e2e
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path
from typing import List, Optional


def discover_tests(test_type: str) -> List[str]:
    """
    Discover test files in the specified test type directory.
    
    Args:
        test_type: 'unit', 'integration', or 'e2e'
        
    Returns:
        List of test file paths
    """
    tests_dir = Path(__file__).parent
    test_type_dir = tests_dir / test_type
    
    if not test_type_dir.exists():
        return []
    
    test_files = []
    for test_file in test_type_dir.rglob("test_*.py"):
        # Convert to relative path from tests directory
        relative_path = test_file.relative_to(tests_dir)
        test_files.append(str(relative_path))
    
    return sorted(test_files)


def run_tests(test_files: List[str], markers: Optional[List[str]] = None, 
              exclude_markers: Optional[List[str]] = None) -> int:
    """
    Run pytest on the specified test files.
    
    Args:
        test_files: List of test file paths
        markers: List of pytest markers to include
        exclude_markers: List of pytest markers to exclude
        
    Returns:
        Exit code from pytest
    """
    if not test_files:
        print(f"No test files found to run.")
        return 0
    
    # Build pytest command
    cmd = [sys.executable, "-m", "pytest"]
    
    # Add test files
    cmd.extend(test_files)
    
    # Add markers
    if markers:
        for marker in markers:
            cmd.extend(["-m", marker])
    
    # Add exclude markers
    if exclude_markers:
        for marker in exclude_markers:
            cmd.extend(["-m", f"not {marker}"])
    
    # Add common pytest options
    cmd.extend([
        "-v",  # Verbose output
        "--tb=short",  # Short traceback format
        "--color=yes",  # Colored output
        "--durations=10",  # Show 10 slowest tests
    ])
    
    print(f"Running: {' '.join(cmd)}")
    print(f"Test files: {len(test_files)}")
    print("-" * 50)
    
    # Run pytest
    result = subprocess.run(cmd, cwd=Path(__file__).parent.parent)
    return result.returncode


def run_unit_tests() -> int:
    """Run all unit tests."""
    print("🔬 Running Unit Tests...")
    test_files = discover_tests("unit")
    return run_tests(test_files, markers=["unit"])


def run_integration_tests() -> int:
    """Run all integration tests."""
    print("🔗 Running Integration Tests...")
    test_files = discover_tests("integration")
    return run_tests(test_files, markers=["integration"])


def run_unit_and_integration_tests() -> int:
    """Run all unit and integration tests (exclude E2E)."""
    print("🧪 Running Unit and Integration Tests...")
    unit_files = discover_tests("unit")
    integration_files = discover_tests("integration")
    all_files = unit_files + integration_files
    
    return run_tests(all_files, exclude_markers=["e2e", "slow"])


def run_all_tests() -> int:
    """Run all tests including E2E."""
    print("🚀 Running All Tests...")
    unit_files = discover_tests("unit")
    integration_files = discover_tests("integration")
    e2e_files = discover_tests("e2e")
    all_files = unit_files + integration_files + e2e_files
    
    return run_tests(all_files)


def main():
    """Main entry point for running tests."""
    parser = argparse.ArgumentParser(
        description="Run Modular Chatbot tests",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m backend.tests                    # Run unit + integration tests
  python -m backend.tests --all              # Run all tests including E2E
  python -m backend.tests --unit-only        # Run only unit tests
  python -m backend.tests --integration-only # Run only integration tests
  python -m backend.tests --no-e2e           # Run unit + integration (exclude E2E)
        """
    )
    
    parser.add_argument(
        "--all", 
        action="store_true",
        help="Run all tests including E2E tests"
    )
    parser.add_argument(
        "--unit-only", 
        action="store_true",
        help="Run only unit tests"
    )
    parser.add_argument(
        "--integration-only", 
        action="store_true",
        help="Run only integration tests"
    )
    parser.add_argument(
        "--no-e2e", 
        action="store_true",
        help="Run unit and integration tests (exclude E2E)"
    )
    parser.add_argument(
        "--list", 
        action="store_true",
        help="List discovered test files without running them"
    )
    
    args = parser.parse_args()
    
    # List test files if requested
    if args.list:
        print("📋 Discovered Test Files:")
        print("\nUnit Tests:")
        for test_file in discover_tests("unit"):
            print(f"  - {test_file}")
        
        print("\nIntegration Tests:")
        for test_file in discover_tests("integration"):
            print(f"  - {test_file}")
        
        print("\nE2E Tests:")
        for test_file in discover_tests("e2e"):
            print(f"  - {test_file}")
        return 0
    
    # Determine which tests to run
    if args.all:
        exit_code = run_all_tests()
    elif args.unit_only:
        exit_code = run_unit_tests()
    elif args.integration_only:
        exit_code = run_integration_tests()
    elif args.no_e2e:
        exit_code = run_unit_and_integration_tests()
    else:
        # Default: run unit and integration tests
        exit_code = run_unit_and_integration_tests()
    
    # Print summary
    print("-" * 50)
    if exit_code == 0:
        print("✅ All tests passed!")
    else:
        print("❌ Some tests failed!")
    
    return exit_code


# Export main function for use in __main__.py
__all__ = ["main", "discover_tests", "run_tests", "run_unit_tests", "run_integration_tests", "run_unit_and_integration_tests", "run_all_tests"]

if __name__ == "__main__":
    sys.exit(main())
