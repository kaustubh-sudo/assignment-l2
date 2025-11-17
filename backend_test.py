#!/usr/bin/env python3
"""
Backend API Testing for Diagram Generation Service
Tests the /api/generate-diagram endpoint to verify bug fixes and functionality
"""

import requests
import json
import sys
import os
from typing import Dict, Any

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
if not BACKEND_URL:
    print("ERROR: Could not determine backend URL from frontend/.env")
    sys.exit(1)

API_BASE = f"{BACKEND_URL}/api"
print(f"Testing backend at: {API_BASE}")

def test_api_endpoint(description: str, diagram_type: str, test_name: str, expected_features: list = None) -> Dict[str, Any]:
    """Test a single API endpoint call and verify advanced features"""
    url = f"{API_BASE}/generate-diagram"
    payload = {
        "description": description,
        "diagram_type": diagram_type
    }
    
    print(f"\n{'='*60}")
    print(f"TEST: {test_name}")
    print(f"URL: {url}")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    print(f"{'='*60}")
    
    try:
        response = requests.post(url, json=payload, timeout=30)
        
        result = {
            "test_name": test_name,
            "status_code": response.status_code,
            "success": response.status_code == 200,
            "response_time": response.elapsed.total_seconds(),
            "content_type": response.headers.get('content-type', ''),
            "response_size": len(response.content),
            "expected_features": expected_features or []
        }
        
        if response.status_code == 200:
            try:
                json_response = response.json()
                result["response_data"] = json_response
                result["has_code"] = "code" in json_response and len(json_response.get("code", "")) > 0
                result["has_kroki_type"] = "kroki_type" in json_response
                result["code_length"] = len(json_response.get("code", ""))
                
                # Check for advanced features
                generated_code = json_response.get("code", "")
                result["generated_code"] = generated_code
                result["is_sophisticated"] = len(generated_code) >= 600  # Critical check
                
                # Feature analysis
                feature_checks = {}
                if diagram_type == "d2":
                    feature_checks["has_classes"] = "classes:" in generated_code
                    feature_checks["has_shapes"] = any(shape in generated_code for shape in ["oval", "diamond", "rectangle", "cylinder"])
                    feature_checks["has_styling"] = "style:" in generated_code and "fill:" in generated_code
                    feature_checks["has_conditionals"] = "Yes" in generated_code and "No" in generated_code
                elif diagram_type == "blockdiag":
                    feature_checks["has_colors"] = "color =" in generated_code
                    feature_checks["has_node_attributes"] = "textcolor" in generated_code
                    feature_checks["has_shapes"] = "roundedbox" in generated_code or "diamond" in generated_code
                    feature_checks["has_conditionals"] = "Yes" in generated_code and "No" in generated_code
                elif diagram_type == "graphviz":
                    feature_checks["has_typed_nodes"] = any(shape in generated_code for shape in ["ellipse", "diamond", "box", "cylinder"])
                    feature_checks["has_colors"] = "fillcolor=" in generated_code and "color=" in generated_code
                    feature_checks["has_conditionals"] = "Yes" in generated_code and "No" in generated_code
                    feature_checks["has_styling"] = "style=" in generated_code
                
                result["feature_checks"] = feature_checks
                result["features_passed"] = sum(feature_checks.values())
                result["total_features"] = len(feature_checks)
                
                print(f"✅ SUCCESS: Status {response.status_code}")
                print(f"   Response time: {result['response_time']:.2f}s")
                print(f"   Code length: {result['code_length']} characters")
                print(f"   Sophisticated: {'✅' if result['is_sophisticated'] else '❌'} (>= 600 chars)")
                print(f"   Kroki type: {json_response.get('kroki_type', 'N/A')}")
                print(f"   Features: {result['features_passed']}/{result['total_features']} passed")
                
                # Show feature details
                for feature, passed in feature_checks.items():
                    status = "✅" if passed else "❌"
                    print(f"     {status} {feature}")
                
                # Show code preview for analysis
                print(f"   Generated code preview:\n{generated_code[:300]}...")
                
            except json.JSONDecodeError as e:
                result["json_error"] = str(e)
                result["raw_response"] = response.text[:500]
                print(f"❌ JSON DECODE ERROR: {e}")
                print(f"   Raw response: {response.text[:200]}...")
        else:
            result["error_response"] = response.text
            print(f"❌ FAILED: Status {response.status_code}")
            print(f"   Error: {response.text}")
            
    except requests.exceptions.RequestException as e:
        result = {
            "test_name": test_name,
            "status_code": None,
            "success": False,
            "error": str(e)
        }
        print(f"❌ REQUEST ERROR: {e}")
    
    return result

def main():
    """Run all test scenarios"""
    print("🚀 Starting Backend API Tests for Diagram Generation")
    print(f"Backend URL: {BACKEND_URL}")
    
    # Test scenarios from the review request - Enhanced D2, BlockDiag, and GraphViz
    test_scenarios = [
        # Complex workflow with conditionals (tests all three types)
        {
            "description": "User logs in, system validates credentials, if valid show dashboard with user profile and activity feed else show error message, user can logout or refresh",
            "diagram_type": "d2",
            "test_name": "Complex D2 Workflow with Conditionals",
            "expected_features": ["classes", "shapes", "styling", "conditional branches", "Yes/No"]
        },
        {
            "description": "User logs in, system validates credentials, if valid show dashboard with user profile and activity feed else show error message, user can logout or refresh",
            "diagram_type": "blockdiag",
            "test_name": "Complex BlockDiag Workflow with Conditionals",
            "expected_features": ["colors", "node attributes", "roundedbox shape", "Yes/No labels"]
        },
        {
            "description": "User logs in, system validates credentials, if valid show dashboard with user profile and activity feed else show error message, user can logout or refresh",
            "diagram_type": "graphviz",
            "test_name": "Complex GraphViz Workflow with Conditionals",
            "expected_features": ["typed nodes", "ellipse/diamond/box", "fillcolor/color attributes", "Yes/No edges"]
        },
        
        # Multi-step process (tests depth)
        {
            "description": "Start process, validate input, check database, process data, generate report, send notification, archive results, complete",
            "diagram_type": "d2",
            "test_name": "Multi-step D2 Process",
            "expected_features": ["sequential connections", "proper node types"]
        },
        {
            "description": "Start process, validate input, check database, process data, generate report, send notification, archive results, complete",
            "diagram_type": "blockdiag",
            "test_name": "Multi-step BlockDiag Process",
            "expected_features": ["all steps captured", "sequential connections"]
        },
        {
            "description": "Start process, validate input, check database, process data, generate report, send notification, archive results, complete",
            "diagram_type": "graphviz",
            "test_name": "Multi-step GraphViz Process",
            "expected_features": ["all steps captured", "proper node types"]
        },
        
        # Error handling workflow
        {
            "description": "Submit request, if valid process else reject, on error retry with backoff, on success save to database",
            "diagram_type": "d2",
            "test_name": "Error Handling D2 Workflow",
            "expected_features": ["error nodes styled differently", "conditional branches"]
        },
        {
            "description": "Submit request, if valid process else reject, on error retry with backoff, on success save to database",
            "diagram_type": "blockdiag",
            "test_name": "Error Handling BlockDiag Workflow",
            "expected_features": ["error nodes styled differently", "conditional branches"]
        },
        {
            "description": "Submit request, if valid process else reject, on error retry with backoff, on success save to database",
            "diagram_type": "graphviz",
            "test_name": "Error Handling GraphViz Workflow",
            "expected_features": ["error nodes styled differently", "conditional branches"]
        }
    ]
    
    results = []
    
    # Run all tests
    for scenario in test_scenarios:
        result = test_api_endpoint(
            scenario["description"],
            scenario["diagram_type"], 
            scenario["test_name"]
        )
        results.append(result)
    
    # Summary
    print(f"\n{'='*80}")
    print("📊 TEST SUMMARY")
    print(f"{'='*80}")
    
    passed = 0
    failed = 0
    critical_issues = []
    
    for result in results:
        status = "✅ PASS" if result["success"] else "❌ FAIL"
        print(f"{status} - {result['test_name']}")
        
        if result["success"]:
            passed += 1
            print(f"      Status: {result['status_code']}, Time: {result.get('response_time', 0):.2f}s")
            if result.get('code_length', 0) > 0:
                print(f"      Generated {result['code_length']} chars of {result.get('response_data', {}).get('kroki_type', 'unknown')} code")
        else:
            failed += 1
            if result['test_name'] == "Complex GraphViz Workflow (Bug Fix Test)":
                critical_issues.append(f"CRITICAL: {result['test_name']} failed - this was the main bug fix target")
            else:
                critical_issues.append(f"FAILED: {result['test_name']}")
            
            if result.get('status_code'):
                print(f"      Status: {result['status_code']}")
                if result.get('error_response'):
                    print(f"      Error: {result['error_response'][:100]}...")
            else:
                print(f"      Connection Error: {result.get('error', 'Unknown')}")
    
    print(f"\n📈 RESULTS: {passed} passed, {failed} failed")
    
    if critical_issues:
        print(f"\n🚨 CRITICAL ISSUES FOUND:")
        for issue in critical_issues:
            print(f"   • {issue}")
    
    # Test basic connectivity
    print(f"\n🔍 CONNECTIVITY TEST")
    try:
        health_response = requests.get(f"{API_BASE}/", timeout=10)
        print(f"✅ Basic connectivity: {health_response.status_code} - {health_response.json()}")
    except Exception as e:
        print(f"❌ Basic connectivity failed: {e}")
        critical_issues.append("CRITICAL: Cannot connect to backend API")
    
    # Return exit code based on results
    if failed > 0:
        print(f"\n❌ TESTING FAILED: {failed} test(s) failed")
        return 1
    else:
        print(f"\n✅ ALL TESTS PASSED: {passed} test(s) successful")
        return 0

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)