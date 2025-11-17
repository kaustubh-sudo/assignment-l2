#!/usr/bin/env python3
"""
Test conditional logic in Mermaid and PlantUML generators
"""

import requests
import json

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

def test_conditional_generation(description, diagram_type):
    """Test conditional generation and show the actual code"""
    url = f"{API_BASE}/generate-diagram"
    payload = {
        "description": description,
        "diagram_type": diagram_type
    }
    
    print(f"\n{'='*80}")
    print(f"Testing {diagram_type.upper()} with conditional description:")
    print(f"'{description}'")
    print(f"{'='*80}")
    
    try:
        response = requests.post(url, json=payload, timeout=30)
        
        if response.status_code == 200:
            json_response = response.json()
            generated_code = json_response.get("code", "")
            
            print(f"✅ SUCCESS: Generated {len(generated_code)} characters")
            print(f"\nGenerated Code:")
            print("-" * 40)
            print(generated_code)
            print("-" * 40)
            
            # Check for conditional patterns
            has_if_else = "if" in generated_code.lower() and ("else" in generated_code.lower() or "otherwise" in generated_code.lower())
            has_yes_no = "yes" in generated_code.lower() and "no" in generated_code.lower()
            has_approved_refund = "approved" in generated_code.lower() and ("refund" in generated_code.lower() or "reject" in generated_code.lower())
            
            print(f"\nConditional Analysis:")
            print(f"  Has if/else pattern: {'✅' if has_if_else else '❌'}")
            print(f"  Has Yes/No branches: {'✅' if has_yes_no else '❌'}")
            print(f"  Has approved/refund logic: {'✅' if has_approved_refund else '❌'}")
            
        else:
            print(f"❌ FAILED: Status {response.status_code}")
            print(f"Error: {response.text}")
            
    except Exception as e:
        print(f"❌ REQUEST ERROR: {e}")

def main():
    # Test the exact scenarios from review request
    test_conditional_generation(
        "Submit order, validate payment, if approved ship product and send confirmation else refund and notify customer",
        "mermaid"
    )
    
    test_conditional_generation(
        "Start application, user authentication, if authorized access resources and perform actions else deny access, end session",
        "plantuml"
    )

if __name__ == "__main__":
    main()