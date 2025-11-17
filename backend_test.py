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

def test_api_endpoint(description: str, diagram_type: str, test_name: str) -> Dict[str, Any]:
    """Test a single API endpoint call"""
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
            "response_size": len(response.content)
        }
        
        if response.status_code == 200:
            try:
                json_response = response.json()
                result["response_data"] = json_response
                result["has_code"] = "code" in json_response and len(json_response.get("code", "")) > 0
                result["has_kroki_type"] = "kroki_type" in json_response
                result["code_length"] = len(json_response.get("code", ""))
                print(f"✅ SUCCESS: Status {response.status_code}")
                print(f"   Response time: {result['response_time']:.2f}s")
                print(f"   Code length: {result['code_length']} characters")
                print(f"   Kroki type: {json_response.get('kroki_type', 'N/A')}")
                if result['code_length'] < 500:  # Show short responses
                    print(f"   Generated code preview:\n{json_response.get('code', '')[:200]}...")
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
    
    # Test scenarios from the review request
    test_scenarios = [
        {
            "description": "A user submits a request. If valid, route to either fast-path processing or slow-path queue. For transient errors: retry with backoff. For fatal errors: send to dead letter queue and raise alert. On success: archive to S3.",
            "diagram_type": "graphviz",
            "test_name": "Complex GraphViz Workflow (Bug Fix Test)"
        },
        {
            "description": "user logs in, checks credentials, shows dashboard, logs out",
            "diagram_type": "graphviz", 
            "test_name": "Simple GraphViz Workflow"
        },
        {
            "description": "user logs in, system validates, database returns data",
            "diagram_type": "mermaid",
            "test_name": "Mermaid Diagram Test"
        },
        {
            "description": "start process, validate input, execute task, complete",
            "diagram_type": "plantuml",
            "test_name": "PlantUML Diagram Test"
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