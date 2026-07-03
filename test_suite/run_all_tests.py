"""
Run All Tests
"""

import subprocess
import sys
import os
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

def run_test(name, script):
    """Run a test script"""
    print("\n" + "=" * 80)
    print(f"🚀 Running: {name}")
    print("=" * 80)
    
    result = subprocess.run(
        [sys.executable, script],
        capture_output=True,
        text=True,
        cwd=Path(__file__).parent.parent
    )
    
    print(result.stdout)
    if result.stderr:
        print("❌ Errors:")
        print(result.stderr)
    
    return result.returncode == 0

def main():
    print("\n" + "=" * 80)
    print("🧪 AI Ad Generator - Test Suite Runner")
    print("=" * 80)
    
    # Check if server is running
    import requests
    try:
        requests.get("http://localhost:8000/health", timeout=2)
        server_running = True
        print("✅ Server is running")
    except:
        server_running = False
        print("⚠️ Server not running. Some tests may fail.")
        print("   Start with: uvicorn app.main:app --reload")
    
    print("\n📋 Available tests:")
    print("  1. Database Test (No server needed)")
    print("  2. API Test (Server needed)")
    print("  3. Full Workflow Test (Server + Database)")
    print("  4. Run All Tests")
    
    choice = input("\nSelect test (1-4): ").strip()
    
    tests_dir = Path(__file__).parent
    
    if choice == "1":
        run_test("Database Test", tests_dir / "test_database.py")
    elif choice == "2":
        if not server_running:
            print("❌ Server must be running for API tests!")
            return
        run_test("API Test", tests_dir / "test_api.py")
    elif choice == "3":
        if not server_running:
            print("❌ Server must be running for workflow tests!")
            return
        run_test("Full Workflow Test", tests_dir / "test_workflow.py")
    elif choice == "4":
        # Run database test first (doesn't need server)
        run_test("Database Test", tests_dir / "test_database.py")
        
        if server_running:
            run_test("API Test", tests_dir / "test_api.py")
            run_test("Full Workflow Test", tests_dir / "test_workflow.py")
        else:
            print("\n⚠️ Skipping API tests (server not running)")
    else:
        print("Invalid choice")
    
    print("\n" + "=" * 80)
    print("✅ Test suite complete!")
    print("=" * 80)

if __name__ == "__main__":
    main()