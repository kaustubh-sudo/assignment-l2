#!/usr/bin/env python3
"""
Backend API Testing for Kroki Diagram Renderer Application
Tests authentication endpoints and diagram generation functionality
"""

import requests
import json
import sys
import os
import base64
import time
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
                print(f"   Expected range: {expected_length_min}-{expected_length_max} chars")
                print(f"   Sophisticated: {'✅' if result['is_sophisticated'] else '❌'} (within expected range)")
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

def test_auth_signup(email: str, password: str, test_name: str, expect_success: bool = True) -> Dict[str, Any]:
    """Test user signup endpoint"""
    url = f"{API_BASE}/auth/signup"
    payload = {
        "email": email,
        "password": password
    }
    
    print(f"\n{'='*60}")
    print(f"AUTH TEST: {test_name}")
    print(f"URL: {url}")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    print(f"{'='*60}")
    
    try:
        response = requests.post(url, json=payload, timeout=30)
        
        result = {
            "test_name": test_name,
            "status_code": response.status_code,
            "success": response.status_code == (201 if expect_success else 400),
            "response_time": response.elapsed.total_seconds(),
            "content_type": response.headers.get('content-type', ''),
            "expect_success": expect_success
        }
        
        if response.status_code in [200, 201]:
            try:
                json_response = response.json()
                result["response_data"] = json_response
                result["has_user_id"] = "id" in json_response
                result["has_email"] = "email" in json_response
                result["has_created_at"] = "created_at" in json_response
                result["email_matches"] = json_response.get("email") == email
                
                print(f"✅ SUCCESS: Status {response.status_code}")
                print(f"   Response time: {result['response_time']:.2f}s")
                print(f"   User ID: {json_response.get('id', 'N/A')}")
                print(f"   Email: {json_response.get('email', 'N/A')}")
                print(f"   Created at: {json_response.get('created_at', 'N/A')}")
                
            except json.JSONDecodeError as e:
                result["json_error"] = str(e)
                result["raw_response"] = response.text[:500]
                print(f"❌ JSON DECODE ERROR: {e}")
        else:
            result["error_response"] = response.text
            if expect_success:
                print(f"❌ FAILED: Status {response.status_code}")
                print(f"   Error: {response.text}")
            else:
                print(f"✅ EXPECTED FAILURE: Status {response.status_code}")
                print(f"   Error: {response.text}")
                result["success"] = True  # Expected failure is success
            
    except requests.exceptions.RequestException as e:
        result = {
            "test_name": test_name,
            "status_code": None,
            "success": False,
            "error": str(e)
        }
        print(f"❌ REQUEST ERROR: {e}")
    
    return result

def test_auth_login(email: str, password: str, test_name: str, expect_success: bool = True) -> Dict[str, Any]:
    """Test user login endpoint"""
    url = f"{API_BASE}/auth/login"
    payload = {
        "email": email,
        "password": password
    }
    
    print(f"\n{'='*60}")
    print(f"AUTH TEST: {test_name}")
    print(f"URL: {url}")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    print(f"{'='*60}")
    
    try:
        response = requests.post(url, json=payload, timeout=30)
        
        result = {
            "test_name": test_name,
            "status_code": response.status_code,
            "success": response.status_code == (200 if expect_success else 401),
            "response_time": response.elapsed.total_seconds(),
            "content_type": response.headers.get('content-type', ''),
            "expect_success": expect_success
        }
        
        if response.status_code == 200:
            try:
                json_response = response.json()
                result["response_data"] = json_response
                result["has_access_token"] = "access_token" in json_response
                result["has_token_type"] = "token_type" in json_response
                result["token_type_correct"] = json_response.get("token_type") == "bearer"
                result["access_token"] = json_response.get("access_token")
                
                print(f"✅ SUCCESS: Status {response.status_code}")
                print(f"   Response time: {result['response_time']:.2f}s")
                print(f"   Token type: {json_response.get('token_type', 'N/A')}")
                print(f"   Access token: {json_response.get('access_token', 'N/A')[:50]}...")
                
            except json.JSONDecodeError as e:
                result["json_error"] = str(e)
                result["raw_response"] = response.text[:500]
                print(f"❌ JSON DECODE ERROR: {e}")
        else:
            result["error_response"] = response.text
            if expect_success:
                print(f"❌ FAILED: Status {response.status_code}")
                print(f"   Error: {response.text}")
            else:
                print(f"✅ EXPECTED FAILURE: Status {response.status_code}")
                print(f"   Error: {response.text}")
                result["success"] = True  # Expected failure is success
            
    except requests.exceptions.RequestException as e:
        result = {
            "test_name": test_name,
            "status_code": None,
            "success": False,
            "error": str(e)
        }
        print(f"❌ REQUEST ERROR: {e}")
    
    return result

def test_auth_me(access_token: str, test_name: str, expect_success: bool = True) -> Dict[str, Any]:
    """Test get current user endpoint"""
    url = f"{API_BASE}/auth/me"
    headers = {}
    if access_token:
        headers["Authorization"] = f"Bearer {access_token}"
    
    print(f"\n{'='*60}")
    print(f"AUTH TEST: {test_name}")
    print(f"URL: {url}")
    print(f"Headers: Authorization: Bearer {access_token[:20] if access_token else 'None'}...")
    print(f"{'='*60}")
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        
        expected_status = 200 if expect_success else (401 if not access_token else 401)
        result = {
            "test_name": test_name,
            "status_code": response.status_code,
            "success": response.status_code == expected_status,
            "response_time": response.elapsed.total_seconds(),
            "content_type": response.headers.get('content-type', ''),
            "expect_success": expect_success
        }
        
        if response.status_code == 200:
            try:
                json_response = response.json()
                result["response_data"] = json_response
                result["has_user_id"] = "id" in json_response
                result["has_email"] = "email" in json_response
                result["has_created_at"] = "created_at" in json_response
                
                print(f"✅ SUCCESS: Status {response.status_code}")
                print(f"   Response time: {result['response_time']:.2f}s")
                print(f"   User ID: {json_response.get('id', 'N/A')}")
                print(f"   Email: {json_response.get('email', 'N/A')}")
                print(f"   Created at: {json_response.get('created_at', 'N/A')}")
                
            except json.JSONDecodeError as e:
                result["json_error"] = str(e)
                result["raw_response"] = response.text[:500]
                print(f"❌ JSON DECODE ERROR: {e}")
        else:
            result["error_response"] = response.text
            if expect_success:
                print(f"❌ FAILED: Status {response.status_code}")
                print(f"   Error: {response.text}")
            else:
                print(f"✅ EXPECTED FAILURE: Status {response.status_code}")
                print(f"   Error: {response.text}")
                result["success"] = True  # Expected failure is success
            
    except requests.exceptions.RequestException as e:
        result = {
            "test_name": test_name,
            "status_code": None,
            "success": False,
            "error": str(e)
        }
        print(f"❌ REQUEST ERROR: {e}")
    
    return result

def run_auth_tests() -> list:
    """Run comprehensive authentication tests"""
    print("🔐 Starting Authentication Tests")
    
    # Generate unique email for testing
    timestamp = int(time.time())
    test_email = f"testuser_{timestamp}@example.com"
    test_password = "testpass123"
    
    auth_results = []
    
    # Test 1: Valid signup
    result = test_auth_signup(test_email, test_password, "Valid Signup", expect_success=True)
    auth_results.append(result)
    
    # Test 2: Duplicate email signup (should fail)
    result = test_auth_signup(test_email, test_password, "Duplicate Email Signup", expect_success=False)
    auth_results.append(result)
    
    # Test 3: Invalid email format (should fail)
    result = test_auth_signup("invalid-email", test_password, "Invalid Email Format", expect_success=False)
    auth_results.append(result)
    
    # Test 4: Password too short (should fail)
    result = test_auth_signup(f"short_{timestamp}@example.com", "12345", "Password Too Short", expect_success=False)
    auth_results.append(result)
    
    # Test 5: Valid login
    result = test_auth_login(test_email, test_password, "Valid Login", expect_success=True)
    auth_results.append(result)
    valid_token = result.get("access_token") if result.get("success") else None
    
    # Test 6: Wrong password (should fail)
    result = test_auth_login(test_email, "wrongpassword", "Wrong Password", expect_success=False)
    auth_results.append(result)
    
    # Test 7: Non-existent email (should fail)
    result = test_auth_login(f"nonexistent_{timestamp}@example.com", test_password, "Non-existent Email", expect_success=False)
    auth_results.append(result)
    
    # Test 8: Get current user with valid token
    if valid_token:
        result = test_auth_me(valid_token, "Valid Token - Get Current User", expect_success=True)
        auth_results.append(result)
    
    # Test 9: Get current user without token (should fail)
    result = test_auth_me("", "No Token - Get Current User", expect_success=False)
    auth_results.append(result)
    
    # Test 10: Get current user with invalid token (should fail)
    result = test_auth_me("invalid.jwt.token", "Invalid Token - Get Current User", expect_success=False)
    auth_results.append(result)
    
    return auth_results

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

def test_status_endpoints() -> list:
    """Test status endpoints"""
    print("\n📊 Starting Status Endpoints Tests")
    
    status_results = []
    
    # Test 1: Create status check
    url = f"{API_BASE}/status"
    payload = {"client_name": "test_client"}
    
    print(f"\n{'='*60}")
    print(f"STATUS TEST: Create Status Check")
    print(f"URL: {url}")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    print(f"{'='*60}")
    
    try:
        response = requests.post(url, json=payload, timeout=30)
        
        result = {
            "test_name": "Create Status Check",
            "status_code": response.status_code,
            "success": response.status_code == 200,
            "response_time": response.elapsed.total_seconds()
        }
        
        if response.status_code == 200:
            json_response = response.json()
            result["response_data"] = json_response
            result["has_id"] = "id" in json_response
            result["has_client_name"] = "client_name" in json_response
            result["has_timestamp"] = "timestamp" in json_response
            
            print(f"✅ SUCCESS: Status {response.status_code}")
            print(f"   Response time: {result['response_time']:.2f}s")
            print(f"   ID: {json_response.get('id', 'N/A')}")
            print(f"   Client: {json_response.get('client_name', 'N/A')}")
        else:
            result["error_response"] = response.text
            print(f"❌ FAILED: Status {response.status_code}")
            print(f"   Error: {response.text}")
            
    except requests.exceptions.RequestException as e:
        result = {
            "test_name": "Create Status Check",
            "status_code": None,
            "success": False,
            "error": str(e)
        }
        print(f"❌ REQUEST ERROR: {e}")
    
    status_results.append(result)
    
    # Test 2: Get status checks
    url = f"{API_BASE}/status"
    
    print(f"\n{'='*60}")
    print(f"STATUS TEST: Get Status Checks")
    print(f"URL: {url}")
    print(f"{'='*60}")
    
    try:
        response = requests.get(url, timeout=30)
        
        result = {
            "test_name": "Get Status Checks",
            "status_code": response.status_code,
            "success": response.status_code == 200,
            "response_time": response.elapsed.total_seconds()
        }
        
        if response.status_code == 200:
            json_response = response.json()
            result["response_data"] = json_response
            result["is_list"] = isinstance(json_response, list)
            result["list_length"] = len(json_response) if isinstance(json_response, list) else 0
            
            print(f"✅ SUCCESS: Status {response.status_code}")
            print(f"   Response time: {result['response_time']:.2f}s")
            print(f"   Status checks count: {result['list_length']}")
        else:
            result["error_response"] = response.text
            print(f"❌ FAILED: Status {response.status_code}")
            print(f"   Error: {response.text}")
            
    except requests.exceptions.RequestException as e:
        result = {
            "test_name": "Get Status Checks",
            "status_code": None,
            "success": False,
            "error": str(e)
        }
        print(f"❌ REQUEST ERROR: {e}")
    
    status_results.append(result)
    
    return status_results

def test_root_endpoint() -> Dict[str, Any]:
    """Test root endpoint"""
    print("\n🏠 Starting Root Endpoint Test")
    
    url = f"{API_BASE}/"
    
    print(f"\n{'='*60}")
    print(f"ROOT TEST: API Root Endpoint")
    print(f"URL: {url}")
    print(f"{'='*60}")
    
    try:
        response = requests.get(url, timeout=30)
        
        result = {
            "test_name": "API Root Endpoint",
            "status_code": response.status_code,
            "success": response.status_code == 200,
            "response_time": response.elapsed.total_seconds()
        }
        
        if response.status_code == 200:
            json_response = response.json()
            result["response_data"] = json_response
            result["has_message"] = "message" in json_response
            result["message_correct"] = json_response.get("message") == "Hello World"
            
            print(f"✅ SUCCESS: Status {response.status_code}")
            print(f"   Response time: {result['response_time']:.2f}s")
            print(f"   Message: {json_response.get('message', 'N/A')}")
        else:
            result["error_response"] = response.text
            print(f"❌ FAILED: Status {response.status_code}")
            print(f"   Error: {response.text}")
            
    except requests.exceptions.RequestException as e:
        result = {
            "test_name": "API Root Endpoint",
            "status_code": None,
            "success": False,
            "error": str(e)
        }
        print(f"❌ REQUEST ERROR: {e}")
    
    return result

def run_diagram_generation_tests() -> list:
    """Run comprehensive diagram generation tests"""
    print("\n🎨 Starting Diagram Generation Tests")
    
    diagram_results = []
    
    # Test scenarios as requested in the review
    test_scenarios = [
        {
            "diagram_type": "graphviz",
            "description": "User logs in, system validates credentials, if valid show dashboard else show error",
            "test_name": "GraphViz - User Login Flow",
            "expected_length_min": 400,
            "expected_length_max": 2000
        },
        {
            "diagram_type": "mermaid", 
            "description": "Start process, validate input, if approved continue else reject, complete task",
            "test_name": "Mermaid - Process Validation Flow",
            "expected_length_min": 200,
            "expected_length_max": 1500
        },
        {
            "diagram_type": "plantuml",
            "description": "User submits form, system processes request, saves to database",
            "test_name": "PlantUML - Form Submission Workflow",
            "expected_length_min": 300,
            "expected_length_max": 1200
        },
        {
            "diagram_type": "pikchr",
            "description": "Simple workflow from start to end with processing step",
            "test_name": "Pikchr - Simple Workflow",
            "expected_length_min": 100,
            "expected_length_max": 800
        },
        # Edge cases
        {
            "diagram_type": "graphviz",
            "description": "This is a very long description that contains many details about a complex business process that involves multiple stakeholders, various decision points, error handling mechanisms, retry logic, parallel processing, data validation, security checks, audit logging, notification systems, and final reporting mechanisms that need to be carefully orchestrated to ensure proper system functionality and user experience",
            "test_name": "GraphViz - Very Long Description",
            "expected_length_min": 500,
            "expected_length_max": 3000
        },
        {
            "diagram_type": "mermaid",
            "description": "Process with special characters: @#$%^&*()_+-=[]{}|;':\",./<>?",
            "test_name": "Mermaid - Special Characters",
            "expected_length_min": 100,
            "expected_length_max": 1000
        },
        {
            "diagram_type": "plantuml",
            "description": "If user is authenticated then check permissions, if admin show admin panel else show user dashboard, if not authenticated redirect to login",
            "test_name": "PlantUML - Complex Conditional Logic",
            "expected_length_min": 400,
            "expected_length_max": 1500
        }
    ]
    
    for scenario in test_scenarios:
        result = test_api_endpoint(
            description=scenario["description"],
            diagram_type=scenario["diagram_type"],
            test_name=scenario["test_name"],
            expected_length_min=scenario["expected_length_min"],
            expected_length_max=scenario["expected_length_max"]
        )
        diagram_results.append(result)
    
    return diagram_results

def main():
    """Run all test scenarios"""
    print("🚀 Starting Backend API Tests for Kroki Diagram Renderer")
    print(f"Backend URL: {BACKEND_URL}")
    
    # Run authentication tests first
    auth_results = run_auth_tests()
    
    # Test basic connectivity
    print(f"\n🔍 CONNECTIVITY TEST")
    try:
        health_response = requests.get(f"{API_BASE}/", timeout=10)
        print(f"✅ Basic connectivity: {health_response.status_code} - {health_response.json()}")
    except Exception as e:
        print(f"❌ Basic connectivity failed: {e}")
    
    # Summary for authentication tests
    print(f"\n{'='*80}")
    print("📊 AUTHENTICATION TEST SUMMARY")
    print(f"{'='*80}")
    
    auth_passed = 0
    auth_failed = 0
    auth_critical_issues = []
    
    for result in auth_results:
        status = "✅ PASS" if result["success"] else "❌ FAIL"
        print(f"{status} - {result['test_name']}")
        
        if result["success"]:
            auth_passed += 1
            print(f"      Status: {result['status_code']}, Time: {result.get('response_time', 0):.2f}s")
        else:
            auth_failed += 1
            auth_critical_issues.append(f"CRITICAL: {result['test_name']} - Authentication test failed")
            
            if result.get('status_code'):
                print(f"      Status: {result['status_code']}")
                if result.get('error_response'):
                    print(f"      Error: {result['error_response'][:100]}...")
            else:
                print(f"      Connection Error: {result.get('error', 'Unknown')}")
    
    print(f"\n📈 AUTH RESULTS: {auth_passed} passed, {auth_failed} failed")
    
    if auth_critical_issues:
        print(f"\n🚨 AUTHENTICATION CRITICAL ISSUES:")
        for issue in auth_critical_issues:
            print(f"   • {issue}")
    
    # Return exit code based on results
    if auth_failed > 0:
        print(f"\n❌ AUTHENTICATION TESTING FAILED: {auth_failed} test(s) failed")
        return 1
    else:
        print(f"\n✅ ALL AUTHENTICATION TESTS PASSED: {auth_passed} test(s) successful")
        return 0

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)