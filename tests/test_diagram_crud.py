"""
Test Suite for Diagram CRUD Operations - US-9 Load Saved Diagram for Editing
Tests the complete flow of creating, retrieving, updating, and deleting diagrams
"""
import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestDiagramCRUD:
    """Tests for Diagram CRUD endpoints - specifically for US-9 Load Saved Diagram"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Create a test user and get auth token"""
        unique_email = f"test_diagram_{uuid.uuid4().hex[:8]}@example.com"
        password = "testpassword123"
        
        # Signup
        signup_resp = requests.post(f"{BASE_URL}/api/auth/signup", json={
            "email": unique_email,
            "password": password
        })
        
        if signup_resp.status_code == 400:
            # User might already exist, try login
            pass
        
        # Login
        login_resp = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": unique_email,
            "password": password
        })
        
        assert login_resp.status_code == 200, f"Login failed: {login_resp.text}"
        return login_resp.json()['access_token']
    
    @pytest.fixture(scope="class")
    def created_diagram(self, auth_token):
        """Create a test diagram and return its data"""
        diagram_data = {
            "title": f"TEST_Diagram_{uuid.uuid4().hex[:8]}",
            "description": "Test diagram for US-9 testing",
            "diagram_type": "graphviz",
            "diagram_code": 'digraph G { A -> B -> C }'
        }
        
        response = requests.post(
            f"{BASE_URL}/api/diagrams",
            json=diagram_data,
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 201, f"Failed to create diagram: {response.text}"
        return response.json()
    
    def test_create_diagram(self, auth_token):
        """Test creating a new diagram"""
        diagram_data = {
            "title": f"TEST_Create_{uuid.uuid4().hex[:8]}",
            "description": "Test diagram creation",
            "diagram_type": "mermaid",
            "diagram_code": "flowchart TD\n    A --> B"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/diagrams",
            json=diagram_data,
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 201
        data = response.json()
        
        # Verify response structure
        assert "id" in data
        assert data["title"] == diagram_data["title"]
        assert data["description"] == diagram_data["description"]
        assert data["diagram_type"] == diagram_data["diagram_type"]
        assert data["diagram_code"] == diagram_data["diagram_code"]
        assert "created_at" in data
        assert "updated_at" in data
        assert "user_id" in data
        
        print(f"✓ Created diagram with ID: {data['id']}")
    
    def test_get_diagram_by_id(self, auth_token, created_diagram):
        """Test GET /api/diagrams/{diagram_id} - Core US-9 functionality"""
        diagram_id = created_diagram["id"]
        
        response = requests.get(
            f"{BASE_URL}/api/diagrams/{diagram_id}",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 200, f"Failed to get diagram: {response.text}"
        data = response.json()
        
        # Verify all fields are returned correctly
        assert data["id"] == diagram_id
        assert data["title"] == created_diagram["title"]
        assert data["description"] == created_diagram["description"]
        assert data["diagram_type"] == created_diagram["diagram_type"]
        assert data["diagram_code"] == created_diagram["diagram_code"]
        assert "created_at" in data
        assert "updated_at" in data
        
        print(f"✓ Successfully retrieved diagram: {data['title']}")
        print(f"  - Type: {data['diagram_type']}")
        print(f"  - Code length: {len(data['diagram_code'])} chars")
    
    def test_get_diagram_not_found(self, auth_token):
        """Test GET /api/diagrams/{diagram_id} with non-existent ID"""
        fake_id = str(uuid.uuid4())
        
        response = requests.get(
            f"{BASE_URL}/api/diagrams/{fake_id}",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
        print("✓ Correctly returns 404 for non-existent diagram")
    
    def test_get_diagram_unauthorized(self, created_diagram):
        """Test GET /api/diagrams/{diagram_id} without auth token"""
        diagram_id = created_diagram["id"]
        
        response = requests.get(f"{BASE_URL}/api/diagrams/{diagram_id}")
        
        assert response.status_code == 403
        print("✓ Correctly returns 403 for unauthorized access")
    
    def test_get_diagram_forbidden_other_user(self, created_diagram):
        """Test GET /api/diagrams/{diagram_id} with different user's token"""
        diagram_id = created_diagram["id"]
        
        # Create another user
        other_email = f"other_user_{uuid.uuid4().hex[:8]}@example.com"
        signup_resp = requests.post(f"{BASE_URL}/api/auth/signup", json={
            "email": other_email,
            "password": "password123"
        })
        
        login_resp = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": other_email,
            "password": "password123"
        })
        
        other_token = login_resp.json()['access_token']
        
        # Try to access first user's diagram
        response = requests.get(
            f"{BASE_URL}/api/diagrams/{diagram_id}",
            headers={"Authorization": f"Bearer {other_token}"}
        )
        
        assert response.status_code == 403
        assert "permission" in response.json()["detail"].lower()
        print("✓ Correctly returns 403 when accessing another user's diagram")
    
    def test_update_diagram(self, auth_token, created_diagram):
        """Test PUT /api/diagrams/{diagram_id} - Update flow for US-9"""
        diagram_id = created_diagram["id"]
        
        updated_data = {
            "title": f"UPDATED_{created_diagram['title']}",
            "description": "Updated description for testing",
            "diagram_type": "graphviz",
            "diagram_code": 'digraph G { A -> B -> C -> D }'
        }
        
        response = requests.put(
            f"{BASE_URL}/api/diagrams/{diagram_id}",
            json=updated_data,
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 200, f"Failed to update diagram: {response.text}"
        data = response.json()
        
        # Verify update was applied
        assert data["title"] == updated_data["title"]
        assert data["description"] == updated_data["description"]
        assert data["diagram_code"] == updated_data["diagram_code"]
        
        # Verify GET returns updated data
        get_response = requests.get(
            f"{BASE_URL}/api/diagrams/{diagram_id}",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert get_response.status_code == 200
        get_data = get_response.json()
        assert get_data["title"] == updated_data["title"]
        
        print(f"✓ Successfully updated diagram: {data['title']}")
    
    def test_list_user_diagrams(self, auth_token):
        """Test GET /api/diagrams - List all user's diagrams"""
        response = requests.get(
            f"{BASE_URL}/api/diagrams",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert isinstance(data, list)
        print(f"✓ User has {len(data)} diagrams")
        
        # Verify structure of list items
        if len(data) > 0:
            item = data[0]
            assert "id" in item
            assert "title" in item
            assert "diagram_type" in item
            assert "created_at" in item
            assert "updated_at" in item
    
    def test_delete_diagram(self, auth_token):
        """Test DELETE /api/diagrams/{diagram_id}"""
        # Create a diagram to delete
        diagram_data = {
            "title": f"TEST_ToDelete_{uuid.uuid4().hex[:8]}",
            "description": "This will be deleted",
            "diagram_type": "graphviz",
            "diagram_code": 'digraph G { X -> Y }'
        }
        
        create_resp = requests.post(
            f"{BASE_URL}/api/diagrams",
            json=diagram_data,
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        diagram_id = create_resp.json()["id"]
        
        # Delete the diagram
        delete_resp = requests.delete(
            f"{BASE_URL}/api/diagrams/{diagram_id}",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert delete_resp.status_code == 204
        
        # Verify it's deleted
        get_resp = requests.get(
            f"{BASE_URL}/api/diagrams/{diagram_id}",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert get_resp.status_code == 404
        print(f"✓ Successfully deleted diagram: {diagram_id}")


class TestDiagramLoadForEditing:
    """Specific tests for US-9: Load Saved Diagram for Editing"""
    
    @pytest.fixture(scope="class")
    def test_user(self):
        """Create a test user for the editing flow"""
        email = f"edit_test_{uuid.uuid4().hex[:8]}@example.com"
        password = "testpassword123"
        
        # Signup
        requests.post(f"{BASE_URL}/api/auth/signup", json={
            "email": email,
            "password": password
        })
        
        # Login
        login_resp = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": email,
            "password": password
        })
        
        return {
            "email": email,
            "password": password,
            "token": login_resp.json()['access_token']
        }
    
    def test_complete_edit_flow(self, test_user):
        """Test the complete flow: Create -> List -> Get -> Edit -> Verify"""
        token = test_user["token"]
        
        # Step 1: Create a diagram
        original_data = {
            "title": "My Test Flowchart",
            "description": "A flowchart for testing the edit flow",
            "diagram_type": "graphviz",
            "diagram_code": 'digraph G {\n  Start -> Process -> End\n}'
        }
        
        create_resp = requests.post(
            f"{BASE_URL}/api/diagrams",
            json=original_data,
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert create_resp.status_code == 201
        created = create_resp.json()
        diagram_id = created["id"]
        print(f"Step 1: Created diagram '{original_data['title']}' with ID: {diagram_id}")
        
        # Step 2: List diagrams and verify it appears
        list_resp = requests.get(
            f"{BASE_URL}/api/diagrams",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert list_resp.status_code == 200
        diagrams = list_resp.json()
        diagram_ids = [d["id"] for d in diagrams]
        assert diagram_id in diagram_ids
        print(f"Step 2: Diagram appears in list (total: {len(diagrams)} diagrams)")
        
        # Step 3: Get diagram by ID (simulates clicking on diagram card)
        get_resp = requests.get(
            f"{BASE_URL}/api/diagrams/{diagram_id}",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert get_resp.status_code == 200
        loaded = get_resp.json()
        
        # Verify all data is loaded correctly
        assert loaded["id"] == diagram_id
        assert loaded["title"] == original_data["title"]
        assert loaded["description"] == original_data["description"]
        assert loaded["diagram_type"] == original_data["diagram_type"]
        assert loaded["diagram_code"] == original_data["diagram_code"]
        print(f"Step 3: Loaded diagram for editing - Title: {loaded['title']}, Type: {loaded['diagram_type']}")
        
        # Step 4: Update the diagram (simulates editing and saving)
        updated_data = {
            "title": "My Updated Flowchart",
            "description": "Updated description after editing",
            "diagram_type": "graphviz",
            "diagram_code": 'digraph G {\n  Start -> Validate -> Process -> Complete -> End\n}'
        }
        
        update_resp = requests.put(
            f"{BASE_URL}/api/diagrams/{diagram_id}",
            json=updated_data,
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert update_resp.status_code == 200
        updated = update_resp.json()
        assert updated["title"] == updated_data["title"]
        print(f"Step 4: Updated diagram - New title: {updated['title']}")
        
        # Step 5: Verify update persisted
        verify_resp = requests.get(
            f"{BASE_URL}/api/diagrams/{diagram_id}",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert verify_resp.status_code == 200
        verified = verify_resp.json()
        assert verified["title"] == updated_data["title"]
        assert verified["description"] == updated_data["description"]
        assert verified["diagram_code"] == updated_data["diagram_code"]
        print(f"Step 5: Verified update persisted correctly")
        
        print("\n✓ Complete edit flow test PASSED")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
