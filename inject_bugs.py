#!/usr/bin/env python3
"""
Bug Injector for Developer Assessment
Injects predefined bugs into the codebase for candidate evaluation.

Usage:
    python inject_bugs.py              # Inject all bugs
    python inject_bugs.py --list       # List all bugs
    python inject_bugs.py --bug AUTH-001  # Inject specific bug
"""

import argparse
import os
import re
import sys
from typing import Dict, List, Tuple

# Bug definitions: bug_id -> (file_path, original_code, buggy_code, description)
BUGS: Dict[str, Dict] = {
    "AUTH-001": {
        "file": "/app/backend/server.py",
        "description": "Email case-sensitive login - Login should be case-insensitive",
        "category": "Authentication",
        "difficulty": "Easy",
        "time_estimate": "1 min",
        "original": '''    # Find user by email
    user_doc = await db.users.find_one({"email": credentials.email.lower()})''',
        "buggy": '''    # Find user by email
    user_doc = await db.users.find_one({"email": credentials.email})''',
    },
    "AUTH-002": {
        "file": "/app/backend/server.py",
        "description": "Duplicate email registration allowed - Should check for existing email",
        "category": "Authentication",
        "difficulty": "Easy",
        "time_estimate": "2 min",
        "original": '''    # Check if user already exists
    existing_user = await db.users.find_one({"email": user_data.email.lower()})
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )''',
        "buggy": '''    # Check if user already exists - DISABLED FOR TESTING
    # existing_user = await db.users.find_one({"email": user_data.email})
    # if existing_user:
    #     raise HTTPException(
    #         status_code=status.HTTP_400_BAD_REQUEST,
    #         detail="Email already registered"
    #     )''',
    },
    "AUTH-003": {
        "file": "/app/frontend/src/context/AuthContext.js",
        "description": "Logout doesn't clear token from localStorage",
        "category": "Authentication",
        "difficulty": "Easy",
        "time_estimate": "1 min",
        "original": '''  const logout = () => {
    localStorage.removeItem('token');
    setToken(null);
    setUser(null);
  };''',
        "buggy": '''  const logout = () => {
    // Token removal disabled
    setToken(null);
    setUser(null);
  };''',
    },
}


def read_file(filepath: str) -> str:
    """Read file content."""
    with open(filepath, 'r') as f:
        return f.read()


def write_file(filepath: str, content: str) -> None:
    """Write content to file."""
    with open(filepath, 'w') as f:
        f.write(content)


def inject_bug(bug_id: str) -> Tuple[bool, str]:
    """
    Inject a single bug into the codebase.
    Returns (success, message).
    """
    if bug_id not in BUGS:
        return False, f"Bug {bug_id} not found"
    
    bug = BUGS[bug_id]
    filepath = bug["file"]
    
    if not os.path.exists(filepath):
        return False, f"File not found: {filepath}"
    
    content = read_file(filepath)
    
    # Check if bug is already injected
    if bug["buggy"] in content:
        return True, f"{bug_id}: Already injected"
    
    # Check if original code exists
    if bug["original"] not in content:
        return False, f"{bug_id}: Original code not found (may already be modified)"
    
    # Inject the bug
    new_content = content.replace(bug["original"], bug["buggy"])
    write_file(filepath, new_content)
    
    return True, f"{bug_id}: Injected successfully"


def inject_all_bugs() -> List[Tuple[str, bool, str]]:
    """Inject all bugs. Returns list of (bug_id, success, message)."""
    results = []
    for bug_id in BUGS:
        success, message = inject_bug(bug_id)
        results.append((bug_id, success, message))
    return results


def list_bugs() -> None:
    """Print all available bugs."""
    print("\n" + "="*70)
    print("AVAILABLE BUGS FOR INJECTION")
    print("="*70)
    
    for bug_id, bug in BUGS.items():
        print(f"\n[{bug_id}]")
        print(f"  Category:    {bug['category']}")
        print(f"  Difficulty:  {bug['difficulty']}")
        print(f"  Time Est:    {bug['time_estimate']}")
        print(f"  File:        {bug['file']}")
        print(f"  Description: {bug['description']}")
    
    print("\n" + "="*70)
    print(f"Total: {len(BUGS)} bugs")
    print("="*70 + "\n")


def check_bug_status(bug_id: str) -> str:
    """Check if a bug is currently injected."""
    if bug_id not in BUGS:
        return "NOT_FOUND"
    
    bug = BUGS[bug_id]
    filepath = bug["file"]
    
    if not os.path.exists(filepath):
        return "FILE_MISSING"
    
    content = read_file(filepath)
    
    if bug["buggy"] in content:
        return "INJECTED"
    elif bug["original"] in content:
        return "FIXED"
    else:
        return "UNKNOWN"


def main():
    parser = argparse.ArgumentParser(description="Bug Injector for Developer Assessment")
    parser.add_argument("--list", action="store_true", help="List all available bugs")
    parser.add_argument("--bug", type=str, help="Inject specific bug by ID (e.g., AUTH-001)")
    parser.add_argument("--status", action="store_true", help="Show current status of all bugs")
    
    args = parser.parse_args()
    
    if args.list:
        list_bugs()
        return
    
    if args.status:
        print("\n" + "="*50)
        print("BUG STATUS")
        print("="*50)
        for bug_id in BUGS:
            status = check_bug_status(bug_id)
            status_icon = "🐛" if status == "INJECTED" else "✅" if status == "FIXED" else "❓"
            print(f"{status_icon} {bug_id}: {status}")
        print("="*50 + "\n")
        return
    
    if args.bug:
        success, message = inject_bug(args.bug)
        icon = "✅" if success else "❌"
        print(f"{icon} {message}")
        return
    
    # Default: inject all bugs
    print("\n" + "="*50)
    print("INJECTING ALL BUGS")
    print("="*50)
    
    results = inject_all_bugs()
    success_count = 0
    
    for bug_id, success, message in results:
        icon = "✅" if success else "❌"
        print(f"{icon} {message}")
        if success:
            success_count += 1
    
    print("="*50)
    print(f"Injected: {success_count}/{len(BUGS)} bugs")
    print("="*50 + "\n")


if __name__ == "__main__":
    main()
