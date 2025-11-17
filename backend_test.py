#!/usr/bin/env python3
"""
Backend API Testing for Diagram Generation Service
Tests the /api/generate-diagram endpoint to verify bug fixes and functionality
"""

import requests
import json
import sys
import os
import base64
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

def test_api_endpoint(description: str, diagram_type: str, test_name: str, expected_features: list = None, expected_length_min: int = 600, expected_length_max: int = 10000) -> Dict[str, Any]:
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
            "expected_features": expected_features or [],
            "expected_length_min": expected_length_min,
            "expected_length_max": expected_length_max
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
                
                result["generated_code"] = generated_code
                result["is_sophisticated"] = expected_length_min <= len(generated_code) <= expected_length_max
                
                # Feature analysis for final 4 diagram types
                feature_checks = {}
                if diagram_type == "graphviz":
                    feature_checks["has_typed_nodes"] = any(shape in generated_code for shape in ["ellipse", "diamond", "box", "cylinder"])
                    feature_checks["has_colors"] = "fillcolor=" in generated_code and "color=" in generated_code
                    feature_checks["has_conditionals"] = "Yes" in generated_code and "No" in generated_code
                    feature_checks["has_styling"] = "style=" in generated_code
                elif diagram_type == "mermaid":
                    feature_checks["has_flowchart"] = "flowchart" in generated_code
                    feature_checks["has_styled_nodes"] = any(style in generated_code for style in ["[", "(", "{", "((", "{{"])
                    feature_checks["has_conditionals"] = ("Yes" in generated_code and "No" in generated_code) or ("|Yes|" in generated_code and "|No|" in generated_code)
                    feature_checks["has_arrows"] = "-->" in generated_code
                elif diagram_type == "plantuml":
                    feature_checks["has_activity_diagram"] = "@startuml" in generated_code and "@enduml" in generated_code
                    feature_checks["has_skinparam"] = "skinparam" in generated_code
                    feature_checks["has_conditionals"] = "if (" in generated_code and "then" in generated_code and "else" in generated_code
                    feature_checks["has_partitions"] = "partition" in generated_code or ":" in generated_code
                elif diagram_type == "excalidraw":
                    feature_checks["has_json_format"] = generated_code.startswith("{") and generated_code.endswith("}")
                    feature_checks["has_rectangles"] = '"type": "rectangle"' in generated_code
                    feature_checks["has_arrows"] = '"type": "arrow"' in generated_code
                    feature_checks["has_elements"] = '"elements":' in generated_code
                
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
                
                # Test Kroki rendering
                kroki_result = test_kroki_rendering(generated_code, diagram_type)
                result.update(kroki_result)
                
                kroki_status = "✅" if kroki_result["kroki_success"] else "❌"
                print(f"   Kroki render: {kroki_status} (HTTP {kroki_result.get('kroki_status', 'N/A')})")
                if not kroki_result["kroki_success"] and kroki_result.get("kroki_error"):
                    print(f"     Error: {kroki_result['kroki_error'][:100]}...")
                
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

def test_kroki_rendering(code: str, diagram_type: str) -> Dict[str, Any]:
    """Test if generated code renders successfully with Kroki API"""
    try:
        # Test with Kroki API using POST method
        kroki_url = f"https://kroki.io/{diagram_type}/svg"
        
        response = requests.post(kroki_url, data=code, headers={'Content-Type': 'text/plain'}, timeout=10)
        
        return {
            "kroki_success": response.status_code == 200,
            "kroki_status": response.status_code,
            "kroki_error": response.text if response.status_code != 200 else None
        }
    except Exception as e:
        return {
            "kroki_success": False,
            "kroki_error": str(e)
        }

def main():
    """Run all test scenarios"""
    print("🚀 Starting Backend API Tests for Final 4 Diagram Types")
    print(f"Backend URL: {BACKEND_URL}")
    
    # Test scenarios from the review request - EXACT 4 scenarios for final implementation
    test_scenarios = [
        # 1. GraphViz - Complex conditional workflow
        {
            "description": "User logs in, system checks credentials, if valid load dashboard with profile and settings else show error and retry, user can logout",
            "diagram_type": "graphviz",
            "test_name": "GraphViz - Complex conditional workflow",
            "expected_features": ["ellipse/diamond/box nodes", "proper shapes", "colors", "conditional branches"],
            "expected_length_min": 800,
            "expected_length_max": 1500
        },
        
        # 2. Mermaid - Multi-step process with conditionals
        {
            "description": "Submit order, validate payment, if approved ship product and send confirmation else refund and notify customer",
            "diagram_type": "mermaid",
            "test_name": "Mermaid - Multi-step process with conditionals",
            "expected_features": ["flowchart with styled nodes", "Yes/No branches", "color-coded types"],
            "expected_length_min": 900,
            "expected_length_max": 1200
        },
        
        # 3. PlantUML - Workflow with partitions
        {
            "description": "Start application, user authentication, if authorized access resources and perform actions else deny access, end session",
            "diagram_type": "plantuml",
            "test_name": "PlantUML - Workflow with partitions",
            "expected_features": ["activity diagram", "skinparam styling", "partitions", "conditional logic"],
            "expected_length_min": 650,
            "expected_length_max": 850
        },
        
        # 4. Excalidraw - Hand-drawn style flowchart
        {
            "description": "Design wireframe, review with team, if approved develop feature else iterate design, test and deploy",
            "diagram_type": "excalidraw",
            "test_name": "Excalidraw - Hand-drawn style flowchart",
            "expected_features": ["JSON format", "rectangles", "arrows", "proper element structure"],
            "expected_length_min": 3000,
            "expected_length_max": 6000
        }
    ]
    
    results = []
    
    # Run all tests
    for scenario in test_scenarios:
        result = test_api_endpoint(
            scenario["description"],
            scenario["diagram_type"], 
            scenario["test_name"],
            scenario.get("expected_features", [])
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
                
                # Check sophistication
                is_sophisticated = result.get('is_sophisticated', False)
                soph_status = "✅" if is_sophisticated else "❌"
                print(f"      Sophisticated: {soph_status} (>= 600 chars)")
                
                # Check features
                features_passed = result.get('features_passed', 0)
                total_features = result.get('total_features', 0)
                if total_features > 0:
                    feature_status = "✅" if features_passed == total_features else "⚠️" if features_passed > 0 else "❌"
                    print(f"      Features: {feature_status} {features_passed}/{total_features}")
                
                # Check Kroki rendering
                kroki_success = result.get('kroki_success', False)
                kroki_status = "✅" if kroki_success else "❌"
                print(f"      Kroki render: {kroki_status}")
                
                # Flag issues
                if not is_sophisticated:
                    critical_issues.append(f"CRITICAL: {result['test_name']} - Generated code too simplistic ({result.get('code_length', 0)} chars < 600)")
                if not kroki_success:
                    critical_issues.append(f"CRITICAL: {result['test_name']} - Kroki rendering failed (HTTP {result.get('kroki_status', 'N/A')})")
                if features_passed < total_features:
                    critical_issues.append(f"WARNING: {result['test_name']} - Missing advanced features ({features_passed}/{total_features})")
        else:
            failed += 1
            critical_issues.append(f"CRITICAL: {result['test_name']} - API call failed")
            
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