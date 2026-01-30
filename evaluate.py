#!/usr/bin/env python3
"""
Evaluator for Developer Assessment
Evaluates candidate's bug fixes and generates reports.

Usage:
    python evaluate.py --candidate "John Doe"           # Basic evaluation
    python evaluate.py --candidate "John Doe" --html    # Generate HTML report
    python evaluate.py --candidate "John Doe" --json    # Generate JSON output
    python evaluate.py --bug AUTH-001                   # Check specific bug
"""

import argparse
import json
import os
from datetime import datetime
from typing import Dict, List, Optional

# Import bug definitions
from inject_bugs import BUGS, check_bug_status


def evaluate_bug(bug_id: str) -> Dict:
    """
    Evaluate a single bug.
    Returns dict with bug info and evaluation result.
    """
    if bug_id not in BUGS:
        return {
            "bug_id": bug_id,
            "status": "NOT_FOUND",
            "fixed": False,
            "points": 0,
            "max_points": 0
        }
    
    bug = BUGS[bug_id]
    status = check_bug_status(bug_id)
    is_fixed = status == "FIXED"
    
    # Use points from bug definition
    max_points = bug.get("points", 5)
    
    return {
        "bug_id": bug_id,
        "category": bug["category"],
        "description": bug["description"],
        "difficulty": bug["difficulty"],
        "file": bug["file"],
        "status": status,
        "fixed": is_fixed,
        "points": max_points if is_fixed else 0,
        "max_points": max_points
    }


def evaluate_all() -> Dict:
    """
    Evaluate all bugs and return comprehensive results.
    """
    results = []
    total_points = 0
    max_points = 0
    fixed_count = 0
    
    for bug_id in BUGS:
        result = evaluate_bug(bug_id)
        results.append(result)
        total_points += result["points"]
        max_points += result["max_points"]
        if result["fixed"]:
            fixed_count += 1
    
    # Group by category
    categories = {}
    for result in results:
        cat = result.get("category", "Unknown")
        if cat not in categories:
            categories[cat] = {"fixed": 0, "total": 0, "points": 0, "max_points": 0}
        categories[cat]["total"] += 1
        categories[cat]["max_points"] += result["max_points"]
        if result["fixed"]:
            categories[cat]["fixed"] += 1
            categories[cat]["points"] += result["points"]
    
    return {
        "timestamp": datetime.now().isoformat(),
        "summary": {
            "total_bugs": len(BUGS),
            "fixed_bugs": fixed_count,
            "total_points": total_points,
            "max_points": max_points,
            "percentage": round((total_points / max_points * 100) if max_points > 0 else 0, 1)
        },
        "categories": categories,
        "details": results
    }


def generate_html_report(evaluation: Dict, candidate: str) -> str:
    """Generate HTML report."""
    summary = evaluation["summary"]
    
    # Status colors
    def get_status_color(fixed):
        return "#22c55e" if fixed else "#ef4444"
    
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Assessment Report - {candidate}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f8fafc; color: #1e293b; line-height: 1.6; padding: 2rem; }}
        .container {{ max-width: 900px; margin: 0 auto; }}
        h1 {{ color: #0f172a; margin-bottom: 0.5rem; }}
        .subtitle {{ color: #64748b; margin-bottom: 2rem; }}
        .card {{ background: white; border-radius: 12px; padding: 1.5rem; margin-bottom: 1.5rem; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }}
        .score-card {{ text-align: center; background: linear-gradient(135deg, #3b82f6, #1d4ed8); color: white; }}
        .score {{ font-size: 4rem; font-weight: bold; }}
        .score-label {{ font-size: 1.25rem; opacity: 0.9; }}
        .progress-bar {{ height: 8px; background: rgba(255,255,255,0.3); border-radius: 4px; margin-top: 1rem; overflow: hidden; }}
        .progress-fill {{ height: 100%; background: white; border-radius: 4px; transition: width 0.5s; }}
        .stats {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 1rem; text-align: center; }}
        .stat {{ padding: 1rem; }}
        .stat-value {{ font-size: 2rem; font-weight: bold; color: #3b82f6; }}
        .stat-label {{ color: #64748b; font-size: 0.875rem; }}
        .bug-list {{ }}
        .bug-item {{ display: flex; align-items: center; padding: 1rem; border-bottom: 1px solid #e2e8f0; }}
        .bug-item:last-child {{ border-bottom: none; }}
        .bug-status {{ width: 12px; height: 12px; border-radius: 50%; margin-right: 1rem; }}
        .bug-info {{ flex: 1; }}
        .bug-id {{ font-weight: 600; color: #0f172a; }}
        .bug-desc {{ color: #64748b; font-size: 0.875rem; }}
        .bug-meta {{ display: flex; gap: 1rem; font-size: 0.75rem; color: #94a3b8; }}
        .badge {{ padding: 0.25rem 0.5rem; border-radius: 4px; font-size: 0.75rem; font-weight: 500; }}
        .badge-fixed {{ background: #dcfce7; color: #166534; }}
        .badge-broken {{ background: #fee2e2; color: #991b1b; }}
        .badge-difficulty {{ background: #f1f5f9; color: #475569; margin-left: 0.5rem; }}
        .category-header {{ font-weight: 600; color: #475569; margin: 1rem 0 0.5rem; padding-top: 1rem; border-top: 1px solid #e2e8f0; }}
        .category-header:first-child {{ border-top: none; padding-top: 0; margin-top: 0; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Assessment Report</h1>
        <p class="subtitle">Candidate: {candidate} | Generated: {evaluation['timestamp'][:19].replace('T', ' ')}</p>
        
        <div class="card score-card">
            <div class="score">{summary['percentage']}%</div>
            <div class="score-label">{summary['total_points']} / {summary['max_points']} Points</div>
            <div class="progress-bar">
                <div class="progress-fill" style="width: {summary['percentage']}%"></div>
            </div>
        </div>
        
        <div class="card">
            <div class="stats">
                <div class="stat">
                    <div class="stat-value">{summary['fixed_bugs']}</div>
                    <div class="stat-label">Bugs Fixed</div>
                </div>
                <div class="stat">
                    <div class="stat-value">{summary['total_bugs'] - summary['fixed_bugs']}</div>
                    <div class="stat-label">Bugs Remaining</div>
                </div>
                <div class="stat">
                    <div class="stat-value">{summary['total_bugs']}</div>
                    <div class="stat-label">Total Bugs</div>
                </div>
            </div>
        </div>
        
        <div class="card">
            <h2 style="margin-bottom: 1rem; color: #0f172a;">Bug Details</h2>
            <div class="bug-list">
"""
    
    # Group bugs by category
    bugs_by_category = {}
    for bug in evaluation["details"]:
        cat = bug.get("category", "Unknown")
        if cat not in bugs_by_category:
            bugs_by_category[cat] = []
        bugs_by_category[cat].append(bug)
    
    for category, bugs in bugs_by_category.items():
        cat_data = evaluation["categories"][category]
        html += f'<div class="category-header">{category} ({cat_data["points"]}/{cat_data["max_points"]} pts)</div>'
        for bug in bugs:
            status_color = get_status_color(bug["fixed"])
            badge_class = "badge-fixed" if bug["fixed"] else "badge-broken"
            badge_text = "FIXED" if bug["fixed"] else "BROKEN"
            
            html += f"""
                <div class="bug-item">
                    <div class="bug-status" style="background: {status_color};"></div>
                    <div class="bug-info">
                        <div class="bug-id">{bug['bug_id']} <span class="badge badge-difficulty">{bug['difficulty']}</span></div>
                        <div class="bug-desc">{bug['description']}</div>
                        <div class="bug-meta">
                            <span>Points: {bug['points']}/{bug['max_points']}</span>
                        </div>
                    </div>
                    <span class="badge {badge_class}">{badge_text}</span>
                </div>
"""
    
    html += """
            </div>
        </div>
    </div>
</body>
</html>
"""
    return html


def print_evaluation(evaluation: Dict, candidate: str) -> None:
    """Print evaluation to console."""
    summary = evaluation["summary"]
    
    print("\n" + "="*60)
    print(f"ASSESSMENT REPORT - {candidate}")
    print("="*60)
    print(f"Timestamp: {evaluation['timestamp'][:19].replace('T', ' ')}")
    print("-"*60)
    
    # Score
    print(f"\n📊 SCORE: {summary['total_points']}/{summary['max_points']} ({summary['percentage']}%)")
    print(f"   Fixed: {summary['fixed_bugs']}/{summary['total_bugs']} bugs")
    
    # Progress bar
    bar_width = 40
    filled = int(bar_width * summary['percentage'] / 100)
    bar = "█" * filled + "░" * (bar_width - filled)
    print(f"   [{bar}]")
    
    # Category breakdown
    print("\n📁 BY CATEGORY:")
    for cat, data in evaluation["categories"].items():
        print(f"   {cat}: {data['fixed']}/{data['total']} fixed ({data['points']}/{data['max_points']} pts)")
    
    # Bug details
    print("\n🐛 BUG DETAILS:")
    for bug in evaluation["details"]:
        icon = "✅" if bug["fixed"] else "❌"
        pts = f"[{bug['points']}/{bug['max_points']}pts]"
        print(f"   {icon} {bug['bug_id']} {pts}: {bug['description'][:45]}...")
    
    print("\n" + "="*60 + "\n")


def main():
    parser = argparse.ArgumentParser(description="Evaluator for Developer Assessment")
    parser.add_argument("--candidate", type=str, default="Anonymous", help="Candidate name")
    parser.add_argument("--bug", type=str, help="Check specific bug by ID")
    parser.add_argument("--html", action="store_true", help="Generate HTML report")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument("--save", type=str, help="Save report to file")
    
    args = parser.parse_args()
    
    # Check specific bug
    if args.bug:
        result = evaluate_bug(args.bug)
        if args.json:
            print(json.dumps(result, indent=2))
        else:
            icon = "✅" if result["fixed"] else "❌"
            print(f"\n{icon} {result['bug_id']}: {result['status']}")
            if result["bug_id"] in BUGS:
                print(f"   Description: {result['description']}")
                print(f"   Difficulty: {result['difficulty']}")
                print(f"   Points: {result['points']}/{result['max_points']}\n")
        return
    
    # Full evaluation
    evaluation = evaluate_all()
    
    # Output format
    if args.json:
        output = json.dumps({
            "candidate": args.candidate,
            **evaluation
        }, indent=2)
        
        if args.save:
            with open(args.save, 'w') as f:
                f.write(output)
            print(f"JSON report saved to: {args.save}")
        else:
            print(output)
    
    elif args.html:
        html = generate_html_report(evaluation, args.candidate)
        
        if args.save:
            with open(args.save, 'w') as f:
                f.write(html)
            print(f"HTML report saved to: {args.save}")
        else:
            # Save to default location
            os.makedirs("/app/reports", exist_ok=True)
            filename = f"/app/reports/{args.candidate.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
            with open(filename, 'w') as f:
                f.write(html)
            print(f"HTML report saved to: {filename}")
    
    else:
        print_evaluation(evaluation, args.candidate)
        
        if args.save:
            # Save console output to file
            import io
            import sys
            
            old_stdout = sys.stdout
            sys.stdout = io.StringIO()
            print_evaluation(evaluation, args.candidate)
            output = sys.stdout.getvalue()
            sys.stdout = old_stdout
            
            with open(args.save, 'w') as f:
                f.write(output)
            print(f"Report saved to: {args.save}")


if __name__ == "__main__":
    main()
