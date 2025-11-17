#!/usr/bin/env python3
"""
Test Kroki rendering with simple examples to isolate the issue
"""

import requests
import base64

def test_kroki_simple():
    """Test with known working examples"""
    
    # Simple D2 example
    d2_code = """
direction: down
A: User
B: System
A -> B: Request
"""
    
    # Simple BlockDiag example  
    blockdiag_code = """
blockdiag {
  A -> B -> C;
}
"""
    
    # Simple GraphViz example
    graphviz_code = """
digraph G {
  A -> B;
}
"""
    
    test_cases = [
        ("d2", d2_code),
        ("blockdiag", blockdiag_code), 
        ("graphviz", graphviz_code)
    ]
    
    for diagram_type, code in test_cases:
        print(f"\n=== Testing {diagram_type} ===")
        print(f"Code: {code}")
        
        try:
            # Try POST method instead
            kroki_url = f"https://kroki.io/{diagram_type}/svg"
            
            response = requests.post(kroki_url, data=code, headers={'Content-Type': 'text/plain'}, timeout=10)
            
            print(f"POST Status: {response.status_code}")
            if response.status_code != 200:
                print(f"POST Error: {response.text[:200]}...")
            else:
                print("✅ POST Success - Kroki rendered successfully")
                continue
                
            # Also try GET method with encoding
            encoded = base64.urlsafe_b64encode(code.encode('utf-8')).decode('ascii')
            kroki_url_get = f"https://kroki.io/{diagram_type}/svg/{encoded}"
            
            response_get = requests.get(kroki_url_get, timeout=10)
            
            print(f"GET Status: {response_get.status_code}")
            if response_get.status_code != 200:
                print(f"GET Error: {response_get.text[:200]}...")
            else:
                print("✅ GET Success - Kroki rendered successfully")
                
        except Exception as e:
            print(f"❌ Exception: {e}")

if __name__ == "__main__":
    test_kroki_simple()