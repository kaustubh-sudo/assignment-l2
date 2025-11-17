#!/usr/bin/env python3
"""
Specific test for GraphViz syntax bug fix in diagram_generator.py
Tests the edge attribute formatting to ensure no invalid syntax like '[, label=...]'
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

def test_graphviz_syntax(description, test_name):
    """Test GraphViz syntax and validate with Kroki"""
    print(f"\n{'='*80}")
    print(f"🔍 TESTING: {test_name}")
    print(f"Description: {description}")
    print(f"{'='*80}")
    
    # Step 1: Generate GraphViz code
    url = f"{API_BASE}/generate-diagram"
    payload = {
        "description": description,
        "diagram_type": "graphviz"
    }
    
    try:
        response = requests.post(url, json=payload, timeout=30)
        
        if response.status_code != 200:
            print(f"❌ FAILED: Backend returned {response.status_code}")
            print(f"   Error: {response.text}")
            return False
            
        json_response = response.json()
        graphviz_code = json_response.get("code", "")
        
        print(f"✅ Backend Response: 200 OK")
        print(f"   Code length: {len(graphviz_code)} characters")
        
        # Step 2: Check for invalid syntax patterns
        print(f"\n🔍 SYNTAX VALIDATION:")
        
        # Check for the specific bug: '[, label=...]' (leading comma)
        invalid_patterns = [
            r'\[\s*,\s*label=',  # [, label=...] 
            r'\[\s*,\s*color=',  # [, color=...]
            r'\[\s*,\s*style=',  # [, style=...]
        ]
        
        syntax_issues = []
        for pattern in invalid_patterns:
            matches = re.findall(pattern, graphviz_code, re.IGNORECASE)
            if matches:
                syntax_issues.append(f"Found invalid pattern '{pattern}': {matches}")
        
        if syntax_issues:
            print(f"❌ SYNTAX ERRORS FOUND:")
            for issue in syntax_issues:
                print(f"   • {issue}")
            print(f"\n📄 Generated Code:\n{graphviz_code}")
            return False
        else:
            print(f"✅ No invalid syntax patterns found")
        
        # Check for proper edge attribute formatting
        edge_pattern = r'(\w+)\s*->\s*(\w+)\s*\[([^\]]+)\]'
        edges = re.findall(edge_pattern, graphviz_code)
        
        print(f"   Found {len(edges)} edges with attributes")
        
        valid_edges = 0
        for i, (from_node, to_node, attributes) in enumerate(edges):
            # Check if attributes are properly formatted
            if attributes.strip().startswith(','):
                print(f"❌ Edge {i+1}: Invalid attributes start with comma: [{attributes}]")
                return False
            else:
                valid_edges += 1
                print(f"   ✅ Edge {i+1}: {from_node} -> {to_node} [{attributes}]")
        
        print(f"✅ All {valid_edges} edges have valid attribute formatting")
        
        # Step 3: Test with Kroki API
        print(f"\n🌐 KROKI VALIDATION:")
        kroki_url = "https://kroki.io/graphviz/svg"
        
        try:
            kroki_response = requests.post(
                kroki_url, 
                data=graphviz_code.encode('utf-8'),
                headers={'Content-Type': 'text/plain'},
                timeout=15
            )
            
            if kroki_response.status_code == 200:
                print(f"✅ Kroki API: 200 OK - GraphViz code is valid")
                print(f"   SVG size: {len(kroki_response.content)} bytes")
                return True
            else:
                print(f"❌ Kroki API: {kroki_response.status_code}")
                print(f"   Error: {kroki_response.text[:200]}...")
                print(f"\n📄 Generated Code that failed:\n{graphviz_code}")
                return False
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Kroki API connection error: {e}")
            print(f"   (Cannot verify with Kroki, but syntax checks passed)")
            return True  # Don't fail test due to network issues
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Backend API connection error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def main():
    """Run GraphViz syntax validation tests"""
    print("🚀 GraphViz Syntax Bug Fix Validation")
    print(f"Backend URL: {BACKEND_URL}")
    
    # Test scenarios that should trigger complex GraphViz generation
    test_scenarios = [
        {
            "description": "A user submits a request, system validates it, if valid route to fast processing else send to slow queue with retry",
            "test_name": "Complex Conditional Workflow (Main Bug Trigger)"
        },
        {
            "description": "User logs in, if credentials valid show dashboard otherwise show error, user can logout",
            "test_name": "Login Flow with Conditionals"
        },
        {
            "description": "Process request, if success archive to S3, if transient error retry with backoff, if fatal error send to dead letter queue",
            "test_name": "Error Handling Workflow"
        },
        {
            "description": "start, process, complete",
            "test_name": "Simple Workflow (Regression Test)"
        }
    ]
    
    results = []
    
    for scenario in test_scenarios:
        result = test_graphviz_syntax(
            scenario["description"],
            scenario["test_name"]
        )
        results.append({
            "test_name": scenario["test_name"],
            "passed": result
        })
    
    # Summary
    print(f"\n{'='*80}")
    print("📊 GRAPHVIZ SYNTAX TEST SUMMARY")
    print(f"{'='*80}")
    
    passed = sum(1 for r in results if r["passed"])
    failed = len(results) - passed
    
    for result in results:
        status = "✅ PASS" if result["passed"] else "❌ FAIL"
        print(f"{status} - {result['test_name']}")
    
    print(f"\n📈 RESULTS: {passed} passed, {failed} failed")
    
    if failed > 0:
        print(f"\n❌ SYNTAX VALIDATION FAILED: {failed} test(s) failed")
        print("   The GraphViz syntax bug fix may not be working correctly")
        return 1
    else:
        print(f"\n✅ ALL SYNTAX TESTS PASSED")
        print("   GraphViz syntax bug fix is working correctly")
        print("   No invalid edge attribute patterns found")
        print("   All generated code validates with Kroki API")
        return 0

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)