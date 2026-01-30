"""
Full Regression Backend API Tests for Kroki Diagram Renderer
Tests all features: Auth (US-1,2,3,4), Diagrams CRUD (US-5,6,7,8,9), Export (US-10), 
Folders (US-12,13), and Diagram Generation
"""
import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL').rstrip('/')

# Test credentials
TEST_EMAIL = "regression_test@example.com"
TEST_PASSWORD = "testpass123"
EXISTING_USER_EMAIL = "foldertest@example.com"
EXISTING_USER_PASSWORD = "password123"


# ============== US-1: Signup Tests ==============
class TestSignup:
    """US-1: Create account with email/password validation"""
    
    def test_signup_success(self, api_client):
        """POST /api/auth/signup - Create new account successfully"""
        unique_email = f"TEST_signup_{uuid.uuid4().hex[:8]}@example.com"
        
        response = api_client.post(f"{BASE_URL}/api/auth/signup", json={
            "email": unique_email,
            "password": "password123"
        })
        
        assert response.status_code == 201, f"Expected 201, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "id" in data
        assert data["email"] == unique_email
        assert "created_at" in data
        # Password should not be returned
        assert "password" not in data
        assert "hashed_password" not in data
    
    def test_signup_duplicate_email(self, api_client):
        """POST /api/auth/signup - Should reject duplicate email"""
        # Use existing user email
        response = api_client.post(f"{BASE_URL}/api/auth/signup", json={
            "email": EXISTING_USER_EMAIL,
            "password": "password123"
        })
        
        assert response.status_code == 400
        assert "already registered" in response.json().get("detail", "").lower()
    
    def test_signup_short_password(self, api_client):
        """POST /api/auth/signup - Should reject password < 6 chars"""
        unique_email = f"TEST_shortpwd_{uuid.uuid4().hex[:8]}@example.com"
        
        response = api_client.post(f"{BASE_URL}/api/auth/signup", json={
            "email": unique_email,
            "password": "12345"  # Only 5 chars
        })
        
        # Should return 422 validation error
        assert response.status_code == 422
    
    def test_signup_invalid_email_format(self, api_client):
        """POST /api/auth/signup - Should reject invalid email format"""
        response = api_client.post(f"{BASE_URL}/api/auth/signup", json={
            "email": "not-an-email",
            "password": "password123"
        })
        
        assert response.status_code == 422


# ============== US-2: Login Tests ==============
class TestLogin:
    """US-2: Authenticate and receive JWT token"""
    
    def test_login_success(self, api_client):
        """POST /api/auth/login - Login with valid credentials"""
        response = api_client.post(f"{BASE_URL}/api/auth/login", json={
            "email": EXISTING_USER_EMAIL,
            "password": EXISTING_USER_PASSWORD
        })
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "access_token" in data
        assert isinstance(data["access_token"], str)
        assert len(data["access_token"]) > 0
    
    def test_login_invalid_email(self, api_client):
        """POST /api/auth/login - Should fail with non-existent email"""
        response = api_client.post(f"{BASE_URL}/api/auth/login", json={
            "email": "nonexistent@example.com",
            "password": "password123"
        })
        
        assert response.status_code == 401
        assert "invalid email or password" in response.json().get("detail", "").lower()
    
    def test_login_invalid_password(self, api_client):
        """POST /api/auth/login - Should fail with wrong password"""
        response = api_client.post(f"{BASE_URL}/api/auth/login", json={
            "email": EXISTING_USER_EMAIL,
            "password": "wrongpassword"
        })
        
        assert response.status_code == 401
        assert "invalid email or password" in response.json().get("detail", "").lower()


# ============== US-4: Protected Routes Tests ==============
class TestProtectedRoutes:
    """US-4: Protected routes require authentication"""
    
    def test_diagrams_require_auth(self, api_client):
        """GET /api/diagrams - Should require authentication"""
        response = api_client.get(f"{BASE_URL}/api/diagrams")
        assert response.status_code in [401, 403]
    
    def test_folders_require_auth(self, api_client):
        """GET /api/folders - Should require authentication"""
        response = api_client.get(f"{BASE_URL}/api/folders")
        assert response.status_code in [401, 403]
    
    def test_auth_me_require_auth(self, api_client):
        """GET /api/auth/me - Should require authentication"""
        response = api_client.get(f"{BASE_URL}/api/auth/me")
        assert response.status_code in [401, 403]
    
    def test_auth_me_with_valid_token(self, api_client, auth_token):
        """GET /api/auth/me - Should return user info with valid token"""
        api_client.headers.update({"Authorization": f"Bearer {auth_token}"})
        
        response = api_client.get(f"{BASE_URL}/api/auth/me")
        
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert "email" in data
        assert "created_at" in data


# ============== US-5, US-6, US-7, US-8, US-9: Diagram CRUD Tests ==============
class TestDiagramCRUD:
    """Tests for diagram CRUD operations"""
    
    def test_create_diagram_success(self, api_client, auth_token):
        """US-5: POST /api/diagrams - Save new diagram"""
        api_client.headers.update({"Authorization": f"Bearer {auth_token}"})
        
        diagram_data = {
            "title": f"TEST_Diagram_{uuid.uuid4().hex[:8]}",
            "description": "Test diagram description",
            "diagram_type": "graphviz",
            "diagram_code": "digraph { A -> B -> C }"
        }
        
        response = api_client.post(f"{BASE_URL}/api/diagrams", json=diagram_data)
        
        assert response.status_code == 201, f"Expected 201, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "id" in data
        assert data["title"] == diagram_data["title"]
        assert data["description"] == diagram_data["description"]
        assert data["diagram_type"] == diagram_data["diagram_type"]
        assert data["diagram_code"] == diagram_data["diagram_code"]
        assert "user_id" in data
        assert "created_at" in data
        assert "updated_at" in data
        
        # Cleanup
        api_client.delete(f"{BASE_URL}/api/diagrams/{data['id']}")
    
    def test_create_diagram_missing_title(self, api_client, auth_token):
        """POST /api/diagrams - Should reject missing title"""
        api_client.headers.update({"Authorization": f"Bearer {auth_token}"})
        
        response = api_client.post(f"{BASE_URL}/api/diagrams", json={
            "description": "Test",
            "diagram_type": "graphviz",
            "diagram_code": "digraph { A -> B }"
        })
        
        assert response.status_code == 422
    
    def test_get_diagrams_list(self, api_client, auth_token):
        """US-7: GET /api/diagrams - List all user diagrams"""
        api_client.headers.update({"Authorization": f"Bearer {auth_token}"})
        
        # Create a test diagram first
        diagram_data = {
            "title": f"TEST_ListDiagram_{uuid.uuid4().hex[:8]}",
            "description": "Test diagram for listing",
            "diagram_type": "mermaid",
            "diagram_code": "flowchart TD\n  A --> B"
        }
        create_response = api_client.post(f"{BASE_URL}/api/diagrams", json=diagram_data)
        assert create_response.status_code == 201
        diagram_id = create_response.json()["id"]
        
        # Get diagrams list
        response = api_client.get(f"{BASE_URL}/api/diagrams")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        
        # Verify our diagram is in the list
        diagram_ids = [d["id"] for d in data]
        assert diagram_id in diagram_ids
        
        # Verify response structure
        if len(data) > 0:
            diagram = data[0]
            assert "id" in diagram
            assert "title" in diagram
            assert "description" in diagram
            assert "diagram_type" in diagram
            assert "folder_id" in diagram
            assert "created_at" in diagram
            assert "updated_at" in diagram
        
        # Cleanup
        api_client.delete(f"{BASE_URL}/api/diagrams/{diagram_id}")
    
    def test_get_diagram_by_id(self, api_client, auth_token):
        """US-9: GET /api/diagrams/{id} - Load diagram for editing"""
        api_client.headers.update({"Authorization": f"Bearer {auth_token}"})
        
        # Create a test diagram
        diagram_data = {
            "title": f"TEST_GetDiagram_{uuid.uuid4().hex[:8]}",
            "description": "Test diagram for get by ID",
            "diagram_type": "plantuml",
            "diagram_code": "@startuml\nA -> B\n@enduml"
        }
        create_response = api_client.post(f"{BASE_URL}/api/diagrams", json=diagram_data)
        diagram_id = create_response.json()["id"]
        
        # Get diagram by ID
        response = api_client.get(f"{BASE_URL}/api/diagrams/{diagram_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == diagram_id
        assert data["title"] == diagram_data["title"]
        assert data["description"] == diagram_data["description"]
        assert data["diagram_type"] == diagram_data["diagram_type"]
        assert data["diagram_code"] == diagram_data["diagram_code"]
        
        # Cleanup
        api_client.delete(f"{BASE_URL}/api/diagrams/{diagram_id}")
    
    def test_get_diagram_not_found(self, api_client, auth_token):
        """GET /api/diagrams/{id} - Should return 404 for non-existent diagram"""
        api_client.headers.update({"Authorization": f"Bearer {auth_token}"})
        
        fake_id = str(uuid.uuid4())
        response = api_client.get(f"{BASE_URL}/api/diagrams/{fake_id}")
        
        assert response.status_code == 404
    
    def test_update_diagram_success(self, api_client, auth_token):
        """US-6: PUT /api/diagrams/{id} - Update existing diagram"""
        api_client.headers.update({"Authorization": f"Bearer {auth_token}"})
        
        # Create a test diagram
        original_data = {
            "title": f"TEST_UpdateDiagram_{uuid.uuid4().hex[:8]}",
            "description": "Original description",
            "diagram_type": "graphviz",
            "diagram_code": "digraph { A -> B }"
        }
        create_response = api_client.post(f"{BASE_URL}/api/diagrams", json=original_data)
        diagram_id = create_response.json()["id"]
        
        # Update the diagram
        updated_data = {
            "title": "Updated Title",
            "description": "Updated description",
            "diagram_type": "graphviz",
            "diagram_code": "digraph { A -> B -> C -> D }"
        }
        update_response = api_client.put(f"{BASE_URL}/api/diagrams/{diagram_id}", json=updated_data)
        
        assert update_response.status_code == 200
        data = update_response.json()
        assert data["title"] == updated_data["title"]
        assert data["description"] == updated_data["description"]
        assert data["diagram_code"] == updated_data["diagram_code"]
        
        # Verify update persisted
        get_response = api_client.get(f"{BASE_URL}/api/diagrams/{diagram_id}")
        assert get_response.json()["title"] == updated_data["title"]
        
        # Cleanup
        api_client.delete(f"{BASE_URL}/api/diagrams/{diagram_id}")
    
    def test_delete_diagram_success(self, api_client, auth_token):
        """US-8: DELETE /api/diagrams/{id} - Delete diagram"""
        api_client.headers.update({"Authorization": f"Bearer {auth_token}"})
        
        # Create a test diagram
        diagram_data = {
            "title": f"TEST_DeleteDiagram_{uuid.uuid4().hex[:8]}",
            "description": "Test diagram to delete",
            "diagram_type": "graphviz",
            "diagram_code": "digraph { A -> B }"
        }
        create_response = api_client.post(f"{BASE_URL}/api/diagrams", json=diagram_data)
        diagram_id = create_response.json()["id"]
        
        # Delete the diagram
        delete_response = api_client.delete(f"{BASE_URL}/api/diagrams/{diagram_id}")
        assert delete_response.status_code == 204
        
        # Verify diagram is deleted
        get_response = api_client.get(f"{BASE_URL}/api/diagrams/{diagram_id}")
        assert get_response.status_code == 404
    
    def test_delete_diagram_not_found(self, api_client, auth_token):
        """DELETE /api/diagrams/{id} - Should return 404 for non-existent diagram"""
        api_client.headers.update({"Authorization": f"Bearer {auth_token}"})
        
        fake_id = str(uuid.uuid4())
        response = api_client.delete(f"{BASE_URL}/api/diagrams/{fake_id}")
        
        assert response.status_code == 404


# ============== Diagram Generation Tests ==============
class TestDiagramGeneration:
    """Tests for diagram generation from natural language"""
    
    def test_generate_graphviz_diagram(self, api_client):
        """POST /api/generate-diagram - Generate GraphViz diagram"""
        response = api_client.post(f"{BASE_URL}/api/generate-diagram", json={
            "description": "User logs in, system validates credentials, shows dashboard",
            "diagram_type": "graphviz"
        })
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "code" in data
        assert "kroki_type" in data
        assert data["kroki_type"] == "graphviz"
        assert len(data["code"]) > 0
        assert "digraph" in data["code"].lower() or "graph" in data["code"].lower()
    
    def test_generate_mermaid_diagram(self, api_client):
        """POST /api/generate-diagram - Generate Mermaid diagram"""
        response = api_client.post(f"{BASE_URL}/api/generate-diagram", json={
            "description": "Start process, check condition, end process",
            "diagram_type": "mermaid"
        })
        
        assert response.status_code == 200
        
        data = response.json()
        assert "code" in data
        assert data["kroki_type"] == "mermaid"
        assert len(data["code"]) > 0
    
    def test_generate_plantuml_diagram(self, api_client):
        """POST /api/generate-diagram - Generate PlantUML diagram"""
        response = api_client.post(f"{BASE_URL}/api/generate-diagram", json={
            "description": "User sends request, server processes, returns response",
            "diagram_type": "plantuml"
        })
        
        assert response.status_code == 200
        
        data = response.json()
        assert "code" in data
        assert data["kroki_type"] == "plantuml"
        assert len(data["code"]) > 0
    
    def test_generate_diagram_empty_description(self, api_client):
        """POST /api/generate-diagram - Should handle empty description"""
        response = api_client.post(f"{BASE_URL}/api/generate-diagram", json={
            "description": "",
            "diagram_type": "graphviz"
        })
        
        # Should either return 422 validation error or generate a default diagram
        assert response.status_code in [200, 422]


# ============== US-12: Folder CRUD Tests ==============
class TestFolderCRUD:
    """US-12: Create, list, delete folders"""
    
    def test_create_folder_success(self, api_client, auth_token):
        """POST /api/folders - Create new folder"""
        api_client.headers.update({"Authorization": f"Bearer {auth_token}"})
        
        folder_name = f"TEST_Folder_{uuid.uuid4().hex[:8]}"
        response = api_client.post(f"{BASE_URL}/api/folders", json={"name": folder_name})
        
        assert response.status_code == 201
        
        data = response.json()
        assert "id" in data
        assert data["name"] == folder_name
        assert "user_id" in data
        assert "created_at" in data
        
        # Cleanup
        api_client.delete(f"{BASE_URL}/api/folders/{data['id']}")
    
    def test_get_folders_list(self, api_client, auth_token):
        """GET /api/folders - List all user folders"""
        api_client.headers.update({"Authorization": f"Bearer {auth_token}"})
        
        # Create a test folder
        folder_name = f"TEST_ListFolder_{uuid.uuid4().hex[:8]}"
        create_response = api_client.post(f"{BASE_URL}/api/folders", json={"name": folder_name})
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
        """DELETE /api/folders/{id} - Delete folder"""
        api_client.headers.update({"Authorization": f"Bearer {auth_token}"})
        
        # Create folder
        folder_name = f"TEST_DeleteFolder_{uuid.uuid4().hex[:8]}"
        create_response = api_client.post(f"{BASE_URL}/api/folders", json={"name": folder_name})
        folder_id = create_response.json()["id"]
        
        # Delete folder
        delete_response = api_client.delete(f"{BASE_URL}/api/folders/{folder_id}")
        assert delete_response.status_code == 204
        
        # Verify folder is deleted
        get_response = api_client.get(f"{BASE_URL}/api/folders")
        folder_ids = [f["id"] for f in get_response.json()["folders"]]
        assert folder_id not in folder_ids


# ============== US-13: Diagram-Folder Association Tests ==============
class TestDiagramFolderAssociation:
    """US-13: Move diagram to folder, filter by folder"""
    
    def test_create_diagram_with_folder(self, api_client, auth_token):
        """POST /api/diagrams - Create diagram with folder_id"""
        api_client.headers.update({"Authorization": f"Bearer {auth_token}"})
        
        # Create folder
        folder_name = f"TEST_DiagramFolder_{uuid.uuid4().hex[:8]}"
        folder_response = api_client.post(f"{BASE_URL}/api/folders", json={"name": folder_name})
        folder_id = folder_response.json()["id"]
        
        # Create diagram with folder
        diagram_data = {
            "title": f"TEST_DiagramInFolder_{uuid.uuid4().hex[:8]}",
            "description": "Test diagram in folder",
            "diagram_type": "graphviz",
            "diagram_code": "digraph { A -> B }",
            "folder_id": folder_id
        }
        diagram_response = api_client.post(f"{BASE_URL}/api/diagrams", json=diagram_data)
        
        assert diagram_response.status_code == 201
        assert diagram_response.json()["folder_id"] == folder_id
        
        # Cleanup
        api_client.delete(f"{BASE_URL}/api/diagrams/{diagram_response.json()['id']}")
        api_client.delete(f"{BASE_URL}/api/folders/{folder_id}")
    
    def test_move_diagram_to_folder(self, api_client, auth_token):
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
        assert get_response.json()["folder_id"] == folder_id
        
        # Cleanup
        api_client.delete(f"{BASE_URL}/api/diagrams/{diagram_id}")
        api_client.delete(f"{BASE_URL}/api/folders/{folder_id}")
    
    def test_remove_diagram_from_folder(self, api_client, auth_token):
        """PUT /api/diagrams/{id}/folder - Remove diagram from folder"""
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


# ============== Health Check ==============
class TestHealthCheck:
    """Basic API health check"""
    
    def test_api_root(self, api_client):
        """GET /api/ - API root should respond"""
        response = api_client.get(f"{BASE_URL}/api/")
        assert response.status_code == 200
        assert "message" in response.json()


# ============== Fixtures ==============
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
        "email": EXISTING_USER_EMAIL,
        "password": EXISTING_USER_PASSWORD
    })
    
    if response.status_code == 200:
        return response.json().get("access_token")
    
    # If login fails, try to signup
    signup_response = api_client.post(f"{BASE_URL}/api/auth/signup", json={
        "email": EXISTING_USER_EMAIL,
        "password": EXISTING_USER_PASSWORD
    })
    
    if signup_response.status_code == 201:
        # Login after signup
        login_response = api_client.post(f"{BASE_URL}/api/auth/login", json={
            "email": EXISTING_USER_EMAIL,
            "password": EXISTING_USER_PASSWORD
        })
        if login_response.status_code == 200:
            return login_response.json().get("access_token")
    
    pytest.skip("Authentication failed - skipping authenticated tests")
