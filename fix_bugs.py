#!/usr/bin/env python3
"""
Bug Fixer for Developer Assessment
Fixes predefined bugs in the codebase (for verification/resetting).

Usage:
    python fix_bugs.py              # Fix all bugs
    python fix_bugs.py --bug AUTH-001  # Fix specific bug
"""

import argparse
import os
import sys
from typing import Dict, List, Tuple

# Import bug definitions from inject_bugs
from inject_bugs import BUGS, read_file, write_file, check_bug_status


def fix_bug(bug_id: str) -> Tuple[bool, str]:
    """
    Fix a single bug in the codebase.
    Returns (success, message).
    """
    if bug_id not in BUGS:
        return False, f"Bug {bug_id} not found"
    
    bug = BUGS[bug_id]
    filepath = bug["file"]
    
    if not os.path.exists(filepath):
        return False, f"File not found: {filepath}"
    
    content = read_file(filepath)
    
    # Check if already fixed
    if bug["original"] in content:
        return True, f"{bug_id}: Already fixed"
    
    # Check if buggy code exists
    if bug["buggy"] not in content:
        return False, f"{bug_id}: Buggy code not found (may already be fixed or modified)"
    
    # Fix the bug
    new_content = content.replace(bug["buggy"], bug["original"])
    write_file(filepath, new_content)
    
    return True, f"{bug_id}: Fixed successfully"


def fix_all_bugs() -> List[Tuple[str, bool, str]]:
    """Fix all bugs. Returns list of (bug_id, success, message)."""
    results = []
    for bug_id in BUGS:
        success, message = fix_bug(bug_id)
        results.append((bug_id, success, message))
    return results


def main():
    parser = argparse.ArgumentParser(description="Bug Fixer for Developer Assessment")
    parser.add_argument("--bug", type=str, help="Fix specific bug by ID (e.g., AUTH-001)")
    parser.add_argument("--status", action="store_true", help="Show current status of all bugs")
    
    args = parser.parse_args()
    
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
        success, message = fix_bug(args.bug)
        icon = "✅" if success else "❌"
        print(f"{icon} {message}")
        return
    
    # Default: fix all bugs
    print("\n" + "="*50)
    print("FIXING ALL BUGS")
    print("="*50)
    
    results = fix_all_bugs()
    success_count = 0
    
    for bug_id, success, message in results:
        icon = "✅" if success else "❌"
        print(f"{icon} {message}")
        if success:
            success_count += 1
    
    print("="*50)
    print(f"Fixed: {success_count}/{len(BUGS)} bugs")
    print("="*50 + "\n")


if __name__ == "__main__":
    main()
