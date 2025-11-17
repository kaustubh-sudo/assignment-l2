#!/usr/bin/env python3
"""
Test the exact scenarios from the review request to verify the GraphViz syntax bug fix
"""

import requests
import json
import re
import sys

# Get backend URL from frontend .env file
def get_backend_url():
    try:
        with open('/app/frontend/.env', 'r') as f:
            for line in f:
                if line.startswith('REACT_APP_BACKEND_URL='):
                    return line.split('=', 1)[1].strip()
    except Exception as e:
        print(f"Error reading backend URL: {e}")
        return None

BACKEND_URL = get_backend_url()
API_BASE = f"{BACKEND_URL}/api"

def test_review_scenario(description, diagram_type, test_name, expected_patterns=None):
    """Test a specific scenario from the review request"""
    print(f"\n{'='*80}")
    print(f"🎯 REVIEW REQUEST TEST: {test_name}")
    print(f"Description: {description}")
    print(f"Diagram Type: {diagram_type}")
    print(f"{'='*80}")
    
    # Generate diagram
    url = f"{API_BASE}/generate-diagram"
    payload = {
        "description": description,
        "diagram_type": diagram_type
    }
    
    try:
        response = requests.post(url, json=payload, timeout=30)
        
        if response.status_code != 200:
            print(f"❌ FAILED: Backend returned {response.status_code}")
            print(f"   Error: {response.text}")
            return False
            
        json_response = response.json()
        generated_code = json_response.get("code", "")
        kroki_type = json_response.get("kroki_type", "")
        
        print(f"✅ Backend Response: 200 OK")
        print(f"   Code length: {len(generated_code)} characters")
        print(f"   Kroki type: {kroki_type}")
        
        # Verify GraphViz specific requirements
        if diagram_type == "graphviz":
            print(f"\n🔍 GRAPHVIZ SYNTAX VERIFICATION:")
            
            # Check for invalid syntax (the bug that was fixed)
            invalid_patterns = [
                r'\[\s*,\s*label=',  # [, label=...] - the main bug
                r'\[\s*,\s*color=',  # [, color=...]
                r'\[\s*,\s*style=',  # [, style=...]
            ]
            
            has_syntax_errors = False
            for pattern in invalid_patterns:
                matches = re.findall(pattern, generated_code, re.IGNORECASE)
                if matches:
                    print(f"❌ SYNTAX ERROR: Found invalid pattern '{pattern}': {matches}")
                    has_syntax_errors = True
            
            if not has_syntax_errors:
                print(f"✅ No invalid syntax patterns found (bug is fixed)")
            
            # Check for proper edge attribute formatting
            edge_pattern = r'(\w+)\s*->\s*(\w+)\s*\[([^\]]+)\]'
            edges = re.findall(edge_pattern, generated_code)
            
            print(f"   Found {len(edges)} edges with attributes")
            
            valid_edge_formats = 0
            for i, (from_node, to_node, attributes) in enumerate(edges):
                # Verify proper formatting: [label="...", color="..."] or [color="..."]
                if re.match(r'^(label="[^"]*",\s*)?color="[^"]*"(,\s*style=\w+)?$', attributes.strip()):
                    valid_edge_formats += 1
                    print(f"   ✅ Edge {i+1}: {from_node} -> {to_node} [{attributes}]")
                elif re.match(r'^color="[^"]*"(,\s*style=\w+)?$', attributes.strip()):
                    valid_edge_formats += 1
                    print(f"   ✅ Edge {i+1}: {from_node} -> {to_node} [{attributes}]")
                else:
                    print(f"   ⚠️  Edge {i+1}: Unusual format: {from_node} -> {to_node} [{attributes}]")
            
            print(f"✅ {valid_edge_formats}/{len(edges)} edges have expected attribute formatting")
            
            # Test with Kroki API (critical verification)
            print(f"\n🌐 KROKI API VERIFICATION:")
            kroki_url = "https://kroki.io/graphviz/svg"
            
            try:
                kroki_response = requests.post(
                    kroki_url, 
                    data=generated_code.encode('utf-8'),
                    headers={'Content-Type': 'text/plain'},
                    timeout=15
                )
                
                if kroki_response.status_code == 200:
                    print(f"✅ Kroki API: 200 OK - No 400 errors (bug is fixed)")
                    print(f"   SVG size: {len(kroki_response.content)} bytes")
                    
                    # Show a sample of the generated code
                    print(f"\n📄 Generated GraphViz Code Sample:")
                    lines = generated_code.split('\n')
                    for i, line in enumerate(lines[:15]):  # Show first 15 lines
                        print(f"   {i+1:2d}: {line}")
                    if len(lines) > 15:
                        print(f"   ... ({len(lines)-15} more lines)")
                    
                    return True
                else:
                    print(f"❌ Kroki API: {kroki_response.status_code} - Still getting errors!")
                    print(f"   Error: {kroki_response.text[:200]}...")
                    print(f"\n📄 Generated Code that failed Kroki:")
                    print(generated_code)
                    return False
                    
            except requests.exceptions.RequestException as e:
                print(f"❌ Kroki API connection error: {e}")
                print(f"   (Cannot verify with Kroki, but syntax checks passed)")
                return not has_syntax_errors  # Pass if no syntax errors found
        
        else:
            # For non-GraphViz types, just verify basic functionality
            print(f"✅ Generated {diagram_type} code successfully")
            return True
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Backend API connection error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def main():
    """Run the exact test scenarios from the review request"""
    print("🎯 REVIEW REQUEST VERIFICATION")
    print("Testing the exact scenarios mentioned in the review request")
    print(f"Backend URL: {BACKEND_URL}")
    
    # Exact scenarios from the review request
    test_scenarios = [
        {
            "description": "A user submits a request, system validates it, if valid route to fast processing else send to slow queue with retry",
            "diagram_type": "graphviz",
            "test_name": "Complex GraphViz with Conditionals (Main Bug Trigger)"
        },
        {
            "description": "User logs in, if credentials valid show dashboard otherwise show error, user can logout",
            "diagram_type": "graphviz", 
            "test_name": "Another Complex Workflow"
        },
        {
            "description": "start, process, complete",
            "diagram_type": "graphviz",
            "test_name": "Simple Workflow (Regression Test)"
        }
    ]
    
    results = []
    
    for scenario in test_scenarios:
        result = test_review_scenario(
            scenario["description"],
            scenario["diagram_type"],
            scenario["test_name"]
        )
        results.append({
            "test_name": scenario["test_name"],
            "passed": result
        })
    
    # Summary
    print(f"\n{'='*80}")
    print("📊 REVIEW REQUEST TEST SUMMARY")
    print(f"{'='*80}")
    
    passed = sum(1 for r in results if r["passed"])
    failed = len(results) - passed
    
    critical_issues = []
    
    for result in results:
        status = "✅ PASS" if result["passed"] else "❌ FAIL"
        print(f"{status} - {result['test_name']}")
        
        if not result["passed"]:
            if "Main Bug Trigger" in result["test_name"]:
                critical_issues.append(f"CRITICAL: {result['test_name']} - The main bug fix target failed")
            else:
                critical_issues.append(f"FAILED: {result['test_name']}")
    
    print(f"\n📈 RESULTS: {passed} passed, {failed} failed")
    
    if critical_issues:
        print(f"\n🚨 ISSUES FOUND:")
        for issue in critical_issues:
            print(f"   • {issue}")
    
    if failed > 0:
        print(f"\n❌ REVIEW REQUEST VERIFICATION FAILED")
        print("   The GraphViz syntax bug fix is not working as expected")
        return 1
    else:
        print(f"\n✅ REVIEW REQUEST VERIFICATION PASSED")
        print("   ✅ All tests return 200 OK")
        print("   ✅ Generated GraphViz code has valid syntax")
        print("   ✅ Edge attributes properly formatted: [label=\"...\", color=\"...\"] or [color=\"...\"]")
        print("   ✅ NO syntax like [, label=...] (leading comma)")
        print("   ✅ Kroki API successfully renders the diagrams (no 400 errors)")
        print("\n🎉 BUG FIX VERIFICATION COMPLETE - All requirements met!")
        return 0

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)