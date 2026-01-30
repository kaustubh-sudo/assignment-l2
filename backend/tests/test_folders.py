"""
Backend API tests for US-12 (Create Folders) and US-13 (Move Diagram to Folder)
Tests folder CRUD operations and diagram-folder associations
"""
import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL').rstrip('/')

# Test credentials
TEST_EMAIL = "foldertest@example.com"
TEST_PASSWORD = "password123"


class TestFolderEndpoints:
    """Tests for folder CRUD operations (US-12)"""
    
    @pytest.fixture(autouse=True)
    def setup(self, api_client, auth_token):
        """Setup for each test"""
        self.client = api_client
        self.token = auth_token
        self.client.headers.update({"Authorization": f"Bearer {self.token}"})
    
    def test_create_folder_success(self, api_client, auth_token):
        """POST /api/folders - Create a new folder"""
        api_client.headers.update({"Authorization": f"Bearer {auth_token}"})
        
        folder_name = f"TEST_Folder_{uuid.uuid4().hex[:8]}"
        response = api_client.post(f"{BASE_URL}/api/folders", json={
            "name": folder_name
        })
        
        assert response.status_code == 201, f"Expected 201, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "id" in data
        assert data["name"] == folder_name
        assert "user_id" in data
        assert "created_at" in data
        
        # Cleanup
        api_client.delete(f"{BASE_URL}/api/folders/{data['id']}")
    
    def test_create_folder_duplicate_name(self, api_client, auth_token):
        """POST /api/folders - Should reject duplicate folder names"""
        api_client.headers.update({"Authorization": f"Bearer {auth_token}"})
        
        folder_name = f"TEST_DuplicateFolder_{uuid.uuid4().hex[:8]}"
        
        # Create first folder
        response1 = api_client.post(f"{BASE_URL}/api/folders", json={"name": folder_name})
        assert response1.status_code == 201
        folder_id = response1.json()["id"]
        
        # Try to create duplicate
        response2 = api_client.post(f"{BASE_URL}/api/folders", json={"name": folder_name})
        assert response2.status_code == 400
        assert "already exists" in response2.json().get("detail", "").lower()
        
        # Cleanup
        api_client.delete(f"{BASE_URL}/api/folders/{folder_id}")
    
    def test_create_folder_empty_name(self, api_client, auth_token):
        """POST /api/folders - Should reject empty folder name"""
        api_client.headers.update({"Authorization": f"Bearer {auth_token}"})
        
        response = api_client.post(f"{BASE_URL}/api/folders", json={"name": ""})
        assert response.status_code == 422  # Validation error
    
    def test_get_folders_list(self, api_client, auth_token):
        """GET /api/folders - List all user folders"""
        api_client.headers.update({"Authorization": f"Bearer {auth_token}"})
        
        # Create a test folder first
        folder_name = f"TEST_ListFolder_{uuid.uuid4().hex[:8]}"
        create_response = api_client.post(f"{BASE_URL}/api/folders", json={"name": folder_name})
        assert create_response.status_code == 201
        folder_id = create_response.json()["id"]
        
        # Get folders list
        response = api_client.get(f"{BASE_URL}/api/folders")
        assert response.status_code == 200
        
        data = response.json()
        assert "folders" in data
        assert isinstance(data["folders"], list)
        
        # Verify our folder is in the list
        folder_names = [f["name"] for f in data["folders"]]
        assert folder_name in folder_names
        
        # Cleanup
        api_client.delete(f"{BASE_URL}/api/folders/{folder_id}")
    
    def test_delete_folder_success(self, api_client, auth_token):
        """DELETE /api/folders/{id} - Delete a folder"""
        api_client.headers.update({"Authorization": f"Bearer {auth_token}"})
        
        # Create folder
        folder_name = f"TEST_DeleteFolder_{uuid.uuid4().hex[:8]}"
        create_response = api_client.post(f"{BASE_URL}/api/folders", json={"name": folder_name})
        assert create_response.status_code == 201
        folder_id = create_response.json()["id"]
        
        # Delete folder
        delete_response = api_client.delete(f"{BASE_URL}/api/folders/{folder_id}")
        assert delete_response.status_code == 204
        
        # Verify folder is gone
        get_response = api_client.get(f"{BASE_URL}/api/folders")
        folder_ids = [f["id"] for f in get_response.json()["folders"]]
        assert folder_id not in folder_ids
    
    def test_delete_folder_not_found(self, api_client, auth_token):
        """DELETE /api/folders/{id} - Should return 404 for non-existent folder"""
        api_client.headers.update({"Authorization": f"Bearer {auth_token}"})
        
        fake_id = str(uuid.uuid4())
        response = api_client.delete(f"{BASE_URL}/api/folders/{fake_id}")
        assert response.status_code == 404
    
    def test_folders_require_auth(self, api_client):
        """Folder endpoints should require authentication"""
        # Remove auth header
        api_client.headers.pop("Authorization", None)
        
        response = api_client.get(f"{BASE_URL}/api/folders")
        assert response.status_code == 401


class TestDiagramFolderAssociation:
    """Tests for diagram-folder associations (US-13)"""
    
    def test_create_diagram_with_folder(self, api_client, auth_token):
        """POST /api/diagrams - Create diagram with folder_id"""
        api_client.headers.update({"Authorization": f"Bearer {auth_token}"})
        
        # Create a folder first
        folder_name = f"TEST_DiagramFolder_{uuid.uuid4().hex[:8]}"
        folder_response = api_client.post(f"{BASE_URL}/api/folders", json={"name": folder_name})
        assert folder_response.status_code == 201
        folder_id = folder_response.json()["id"]
        
        # Create diagram with folder_id
        diagram_data = {
            "title": f"TEST_Diagram_{uuid.uuid4().hex[:8]}",
            "description": "Test diagram in folder",
            "diagram_type": "graphviz",
            "diagram_code": "digraph { A -> B }",
            "folder_id": folder_id
        }
        
        diagram_response = api_client.post(f"{BASE_URL}/api/diagrams", json=diagram_data)
        assert diagram_response.status_code == 201
        
        diagram = diagram_response.json()
        assert diagram["folder_id"] == folder_id
        
        # Cleanup
        api_client.delete(f"{BASE_URL}/api/diagrams/{diagram['id']}")
        api_client.delete(f"{BASE_URL}/api/folders/{folder_id}")
    
    def test_create_diagram_without_folder(self, api_client, auth_token):
        """POST /api/diagrams - Create diagram without folder_id"""
        api_client.headers.update({"Authorization": f"Bearer {auth_token}"})
        
        diagram_data = {
            "title": f"TEST_NoFolderDiagram_{uuid.uuid4().hex[:8]}",
            "description": "Test diagram without folder",
            "diagram_type": "graphviz",
            "diagram_code": "digraph { A -> B }"
        }
        
        response = api_client.post(f"{BASE_URL}/api/diagrams", json=diagram_data)
        assert response.status_code == 201
        
        diagram = response.json()
        assert diagram["folder_id"] is None
        
        # Cleanup
        api_client.delete(f"{BASE_URL}/api/diagrams/{diagram['id']}")
    
    def test_update_diagram_folder(self, api_client, auth_token):
        """PUT /api/diagrams/{id}/folder - Move diagram to folder"""
        api_client.headers.update({"Authorization": f"Bearer {auth_token}"})
        
        # Create folder
        folder_name = f"TEST_MoveFolder_{uuid.uuid4().hex[:8]}"
        folder_response = api_client.post(f"{BASE_URL}/api/folders", json={"name": folder_name})
        folder_id = folder_response.json()["id"]
        
        # Create diagram without folder
        diagram_data = {
            "title": f"TEST_MoveDiagram_{uuid.uuid4().hex[:8]}",
            "description": "Test diagram to move",
            "diagram_type": "graphviz",
            "diagram_code": "digraph { A -> B }"
        }
        diagram_response = api_client.post(f"{BASE_URL}/api/diagrams", json=diagram_data)
        diagram_id = diagram_response.json()["id"]
        
        # Move diagram to folder
        move_response = api_client.put(
            f"{BASE_URL}/api/diagrams/{diagram_id}/folder",
            json={"folder_id": folder_id}
        )
        assert move_response.status_code == 200
        
        # Verify diagram is in folder
        get_response = api_client.get(f"{BASE_URL}/api/diagrams/{diagram_id}")
        assert get_response.status_code == 200
        assert get_response.json()["folder_id"] == folder_id
        
        # Cleanup
        api_client.delete(f"{BASE_URL}/api/diagrams/{diagram_id}")
        api_client.delete(f"{BASE_URL}/api/folders/{folder_id}")
    
    def test_remove_diagram_from_folder(self, api_client, auth_token):
        """PUT /api/diagrams/{id}/folder - Remove diagram from folder (set to null)"""
        api_client.headers.update({"Authorization": f"Bearer {auth_token}"})
        
        # Create folder
        folder_name = f"TEST_RemoveFolder_{uuid.uuid4().hex[:8]}"
        folder_response = api_client.post(f"{BASE_URL}/api/folders", json={"name": folder_name})
        folder_id = folder_response.json()["id"]
        
        # Create diagram in folder
        diagram_data = {
            "title": f"TEST_RemoveDiagram_{uuid.uuid4().hex[:8]}",
            "description": "Test diagram to remove from folder",
            "diagram_type": "graphviz",
            "diagram_code": "digraph { A -> B }",
            "folder_id": folder_id
        }
        diagram_response = api_client.post(f"{BASE_URL}/api/diagrams", json=diagram_data)
        diagram_id = diagram_response.json()["id"]
        
        # Remove from folder
        remove_response = api_client.put(
            f"{BASE_URL}/api/diagrams/{diagram_id}/folder",
            json={"folder_id": None}
        )
        assert remove_response.status_code == 200
        
        # Verify diagram has no folder
        get_response = api_client.get(f"{BASE_URL}/api/diagrams/{diagram_id}")
        assert get_response.json()["folder_id"] is None
        
        # Cleanup
        api_client.delete(f"{BASE_URL}/api/diagrams/{diagram_id}")
        api_client.delete(f"{BASE_URL}/api/folders/{folder_id}")
    
    def test_delete_folder_clears_diagram_folder_id(self, api_client, auth_token):
        """DELETE /api/folders/{id} - Diagrams in folder should have folder_id set to null"""
        api_client.headers.update({"Authorization": f"Bearer {auth_token}"})
        
        # Create folder
        folder_name = f"TEST_ClearFolder_{uuid.uuid4().hex[:8]}"
        folder_response = api_client.post(f"{BASE_URL}/api/folders", json={"name": folder_name})
        folder_id = folder_response.json()["id"]
        
        # Create diagram in folder
        diagram_data = {
            "title": f"TEST_ClearDiagram_{uuid.uuid4().hex[:8]}",
            "description": "Test diagram in folder to be deleted",
            "diagram_type": "graphviz",
            "diagram_code": "digraph { A -> B }",
            "folder_id": folder_id
        }
        diagram_response = api_client.post(f"{BASE_URL}/api/diagrams", json=diagram_data)
        diagram_id = diagram_response.json()["id"]
        
        # Delete folder
        delete_response = api_client.delete(f"{BASE_URL}/api/folders/{folder_id}")
        assert delete_response.status_code == 204
        
        # Verify diagram folder_id is now null
        get_response = api_client.get(f"{BASE_URL}/api/diagrams/{diagram_id}")
        assert get_response.json()["folder_id"] is None
        
        # Cleanup
        api_client.delete(f"{BASE_URL}/api/diagrams/{diagram_id}")
    
    def test_update_diagram_with_invalid_folder(self, api_client, auth_token):
        """PUT /api/diagrams/{id}/folder - Should reject invalid folder_id"""
        api_client.headers.update({"Authorization": f"Bearer {auth_token}"})
        
        # Create diagram
        diagram_data = {
            "title": f"TEST_InvalidFolder_{uuid.uuid4().hex[:8]}",
            "description": "Test diagram",
            "diagram_type": "graphviz",
            "diagram_code": "digraph { A -> B }"
        }
        diagram_response = api_client.post(f"{BASE_URL}/api/diagrams", json=diagram_data)
        diagram_id = diagram_response.json()["id"]
        
        # Try to move to non-existent folder
        fake_folder_id = str(uuid.uuid4())
        move_response = api_client.put(
            f"{BASE_URL}/api/diagrams/{diagram_id}/folder",
            json={"folder_id": fake_folder_id}
        )
        assert move_response.status_code == 404
        
        # Cleanup
        api_client.delete(f"{BASE_URL}/api/diagrams/{diagram_id}")
    
    def test_diagrams_list_includes_folder_id(self, api_client, auth_token):
        """GET /api/diagrams - Response should include folder_id field"""
        api_client.headers.update({"Authorization": f"Bearer {auth_token}"})
        
        response = api_client.get(f"{BASE_URL}/api/diagrams")
        assert response.status_code == 200
        
        diagrams = response.json()
        if len(diagrams) > 0:
            # Check that folder_id field exists (can be null or string)
            assert "folder_id" in diagrams[0]


# Fixtures
@pytest.fixture
def api_client():
    """Shared requests session"""
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})
    return session


@pytest.fixture
def auth_token(api_client):
    """Get authentication token"""
    # Try to login first
    response = api_client.post(f"{BASE_URL}/api/auth/login", json={
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD
    })
    
    if response.status_code == 200:
        return response.json().get("access_token")
    
    # If login fails, try to signup
    signup_response = api_client.post(f"{BASE_URL}/api/auth/signup", json={
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD
    })
    
    if signup_response.status_code == 201:
        # Login after signup
        login_response = api_client.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        if login_response.status_code == 200:
            return login_response.json().get("access_token")
    
    pytest.skip("Authentication failed - skipping authenticated tests")
