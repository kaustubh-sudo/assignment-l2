#!/usr/bin/env python3
"""
Bug Manager for Developer Assessment
Manual control: check status, inject/fix individual or all bugs.

Usage:
    python manager.py status              # Show status of all bugs
    python manager.py inject              # Inject all bugs
    python manager.py inject AUTH-001     # Inject specific bug
    python manager.py fix                 # Fix all bugs
    python manager.py fix AUTH-001        # Fix specific bug
    python manager.py reset               # Reset to clean state (fix all)
    python manager.py list                # List all bug definitions
    python manager.py info AUTH-001       # Show detailed info about a bug
"""

import argparse
import sys

from inject_bugs import (
    BUGS, 
    inject_bug, 
    inject_all_bugs, 
    list_bugs, 
    check_bug_status,
    read_file
)
from fix_bugs import fix_bug, fix_all_bugs


def show_status():
    """Show current status of all bugs."""
    print("\n" + "="*70)
    print("BUG STATUS OVERVIEW")
    print("="*70)
    
    injected = 0
    fixed = 0
    unknown = 0
    
    for bug_id, bug in BUGS.items():
        status = check_bug_status(bug_id)
        
        if status == "INJECTED":
            icon = "🐛"
            color_status = "INJECTED (Bug Active)"
            injected += 1
        elif status == "FIXED":
            icon = "✅"
            color_status = "FIXED (Clean)"
            fixed += 1
        else:
            icon = "❓"
            color_status = f"UNKNOWN ({status})"
            unknown += 1
        
        print(f"\n{icon} [{bug_id}] {color_status}")
        print(f"   Category:    {bug['category']}")
        print(f"   Difficulty:  {bug['difficulty']}")
        print(f"   Description: {bug['description']}")
        print(f"   File:        {bug['file']}")
    
    print("\n" + "-"*70)
    print(f"Summary: {injected} injected | {fixed} fixed | {unknown} unknown")
    print("="*70 + "\n")


def show_bug_info(bug_id: str):
    """Show detailed information about a specific bug."""
    if bug_id not in BUGS:
        print(f"❌ Bug {bug_id} not found")
        return
    
    bug = BUGS[bug_id]
    status = check_bug_status(bug_id)
    
    print("\n" + "="*70)
    print(f"BUG INFORMATION: {bug_id}")
    print("="*70)
    
    status_icon = "🐛" if status == "INJECTED" else "✅" if status == "FIXED" else "❓"
    print(f"\nStatus:      {status_icon} {status}")
    print(f"Category:    {bug['category']}")
    print(f"Difficulty:  {bug['difficulty']}")
    print(f"Time Est:    {bug['time_estimate']}")
    print(f"File:        {bug['file']}")
    print(f"Description: {bug['description']}")
    
    print("\n" + "-"*70)
    print("ORIGINAL CODE (Fixed State):")
    print("-"*70)
    print(bug['original'])
    
    print("\n" + "-"*70)
    print("BUGGY CODE (Injected State):")
    print("-"*70)
    print(bug['buggy'])
    
    print("\n" + "="*70 + "\n")


def cmd_inject(bug_id: str = None):
    """Handle inject command."""
    if bug_id:
        if bug_id not in BUGS:
            print(f"❌ Bug {bug_id} not found")
            return
        success, message = inject_bug(bug_id)
        icon = "✅" if success else "❌"
        print(f"{icon} {message}")
    else:
        print("\n" + "="*50)
        print("INJECTING ALL BUGS")
        print("="*50)
        
        results = inject_all_bugs()
        success_count = sum(1 for _, success, _ in results if success)
        
        for bug_id, success, message in results:
            icon = "✅" if success else "❌"
            print(f"{icon} {message}")
        
        print("="*50)
        print(f"Result: {success_count}/{len(BUGS)} bugs injected")
        print("="*50 + "\n")


def cmd_fix(bug_id: str = None):
    """Handle fix command."""
    if bug_id:
        if bug_id not in BUGS:
            print(f"❌ Bug {bug_id} not found")
            return
        success, message = fix_bug(bug_id)
        icon = "✅" if success else "❌"
        print(f"{icon} {message}")
    else:
        print("\n" + "="*50)
        print("FIXING ALL BUGS")
        print("="*50)
        
        results = fix_all_bugs()
        success_count = sum(1 for _, success, _ in results if success)
        
        for bug_id, success, message in results:
            icon = "✅" if success else "❌"
            print(f"{icon} {message}")
        
        print("="*50)
        print(f"Result: {success_count}/{len(BUGS)} bugs fixed")
        print("="*50 + "\n")


def main():
    parser = argparse.ArgumentParser(
        description="Bug Manager for Developer Assessment",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python manager.py status              # Show status of all bugs
    python manager.py inject              # Inject all bugs
    python manager.py inject AUTH-001     # Inject specific bug
    python manager.py fix                 # Fix all bugs
    python manager.py fix AUTH-001        # Fix specific bug
    python manager.py reset               # Reset to clean state (fix all)
    python manager.py list                # List all bug definitions
    python manager.py info AUTH-001       # Show detailed info about a bug
        """
    )
    
    parser.add_argument("command", nargs="?", default="status",
                       choices=["status", "inject", "fix", "reset", "list", "info"],
                       help="Command to execute")
    parser.add_argument("bug_id", nargs="?", help="Bug ID (e.g., AUTH-001)")
    
    args = parser.parse_args()
    
    if args.command == "status":
        show_status()
    
    elif args.command == "inject":
        cmd_inject(args.bug_id)
    
    elif args.command == "fix" or args.command == "reset":
        cmd_fix(args.bug_id)
    
    elif args.command == "list":
        list_bugs()
    
    elif args.command == "info":
        if args.bug_id:
            show_bug_info(args.bug_id)
        else:
            print("❌ Please specify a bug ID: python manager.py info AUTH-001")


if __name__ == "__main__":
    main()
