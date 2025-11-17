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
            # Encode the diagram code
            encoded = base64.urlsafe_b64encode(code.encode('utf-8')).decode('ascii')
            
            # Test with Kroki API
            kroki_url = f"https://kroki.io/{diagram_type}/svg/{encoded}"
            print(f"URL: {kroki_url}")
            
            response = requests.get(kroki_url, timeout=10)
            
            print(f"Status: {response.status_code}")
            if response.status_code != 200:
                print(f"Error: {response.text[:200]}...")
            else:
                print("✅ Success - Kroki rendered successfully")
                
        except Exception as e:
            print(f"❌ Exception: {e}")

if __name__ == "__main__":
    test_kroki_simple()