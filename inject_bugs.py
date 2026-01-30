#!/usr/bin/env python3
"""
Bug Injector for Developer Assessment
Injects predefined bugs into the codebase for candidate evaluation.

Usage:
    python inject_bugs.py              # Inject all bugs
    python inject_bugs.py --list       # List all bugs
    python inject_bugs.py --bug AUTH-001  # Inject specific bug
"""

import argparse
import os
import re
import sys
from typing import Dict, List, Tuple

# Bug definitions: bug_id -> (file_path, original_code, buggy_code, description)
BUGS: Dict[str, Dict] = {
    # ============== AUTHENTICATION BUGS ==============
    "AUTH-001": {
        "file": "/app/backend/server.py",
        "description": "Email case-sensitive login - Login should be case-insensitive",
        "category": "Authentication",
        "difficulty": "Easy",
        "points": 5,
        "time_estimate": "1 min",
        "original": '''    # Find user by email
    user_doc = await db.users.find_one({"email": credentials.email.lower()})''',
        "buggy": '''    # Find user by email
    user_doc = await db.users.find_one({"email": credentials.email})''',
    },
    "AUTH-002": {
        "file": "/app/backend/server.py",
        "description": "Duplicate email registration allowed - Should check for existing email",
        "category": "Authentication",
        "difficulty": "Easy",
        "points": 5,
        "time_estimate": "2 min",
        "original": '''    # Check if user already exists
    existing_user = await db.users.find_one({"email": user_data.email.lower()})
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )''',
        "buggy": '''    # Check if user already exists - DISABLED FOR TESTING
    # existing_user = await db.users.find_one({"email": user_data.email})
    # if existing_user:
    #     raise HTTPException(
    #         status_code=status.HTTP_400_BAD_REQUEST,
    #         detail="Email already registered"
    #     )''',
    },
    "AUTH-003": {
        "file": "/app/frontend/src/context/AuthContext.js",
        "description": "Logout doesn't clear token from localStorage",
        "category": "Authentication",
        "difficulty": "Easy",
        "points": 5,
        "time_estimate": "1 min",
        "original": '''  const logout = () => {
    localStorage.removeItem('token');
    setToken(null);
    setUser(null);
  };''',
        "buggy": '''  const logout = () => {
    // Token removal disabled
    setToken(null);
    setUser(null);
  };''',
    },
    "AUTH-004": {
        "file": "/app/backend/server.py",
        "description": "Password minimum length not enforced - Should require 6+ characters",
        "category": "Authentication",
        "difficulty": "Easy",
        "points": 5,
        "time_estimate": "1 min",
        "original": '''@api_router.post("/auth/signup", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def signup(user_data: UserCreate):
    """
    Register a new user with email and password.
    Password must be at least 6 characters.
    """
    # Validate password length
    if len(user_data.password) < 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 6 characters"
        )
    
    # Check if user already exists''',
        "buggy": '''@api_router.post("/auth/signup", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def signup(user_data: UserCreate):
    """
    Register a new user with email and password.
    Password must be at least 6 characters.
    """
    # Password validation disabled for testing
    
    # Check if user already exists''',
    },
    
    # ============== SAVE/LOAD BUGS ==============
    "SAVE-001": {
        "file": "/app/backend/server.py",
        "description": "Save creates duplicate entries - Should update existing diagram with same title",
        "category": "Save/Load",
        "difficulty": "Hard",
        "points": 15,
        "time_estimate": "4 min",
        "original": '''@api_router.post("/diagrams", response_model=DiagramResponse, status_code=status.HTTP_201_CREATED)
async def create_diagram(
    diagram_data: DiagramCreate,
    current_user: TokenData = Depends(get_current_user)
):
    """
    Save a new diagram for the authenticated user.
    Requires valid JWT token in Authorization header.
    """
    # Check for existing diagram with same title (prevent duplicates)
    existing_diagram = await db.diagrams.find_one({
        "user_id": current_user.user_id,
        "title": diagram_data.title
    })
    
    if existing_diagram:
        # Update existing diagram instead of creating duplicate
        now = datetime.now(timezone.utc)
        update_data = {
            "description": diagram_data.description,
            "diagram_type": diagram_data.diagram_type,
            "diagram_code": diagram_data.diagram_code,
            "folder_id": diagram_data.folder_id,
            "updated_at": now.isoformat()
        }
        
        await db.diagrams.update_one(
            {"id": existing_diagram["id"]},
            {"$set": update_data}
        )
        
        created_at = existing_diagram['created_at']
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at)
        
        logger.info(f"Diagram updated (duplicate title): {existing_diagram['id']} by user {current_user.user_id}")
        
        return DiagramResponse(
            id=existing_diagram['id'],
            user_id=current_user.user_id,
            title=diagram_data.title,
            description=diagram_data.description,
            diagram_type=diagram_data.diagram_type,
            diagram_code=diagram_data.diagram_code,
            folder_id=diagram_data.folder_id,
            created_at=created_at,
            updated_at=now
        )
    
    # Validate folder_id if provided''',
        "buggy": '''@api_router.post("/diagrams", response_model=DiagramResponse, status_code=status.HTTP_201_CREATED)
async def create_diagram(
    diagram_data: DiagramCreate,
    current_user: TokenData = Depends(get_current_user)
):
    """
    Save a new diagram for the authenticated user.
    Requires valid JWT token in Authorization header.
    """
    # Duplicate check disabled - allows multiple diagrams with same title
    
    # Validate folder_id if provided''',
    },
    "SAVE-002": {
        "file": "/app/frontend/src/pages/DiagramRenderer.js",
        "description": "Load diagram doesn't populate textarea - diagram code not loaded properly",
        "category": "Save/Load",
        "difficulty": "Medium",
        "points": 10,
        "time_estimate": "2 min",
        "original": '''          if (response.ok) {
            const data = await response.json();
            setDiagramType(data.diagram_type);
            setGeneratedCode(data.diagram_code);
            setUserInput(data.description || '');
            setSavedDiagram({''',
        "buggy": '''          if (response.ok) {
            const data = await response.json();
            setDiagramType(data.diagram_type);
            setGeneratedCode(data.diagram_code);
            // BUG: Not setting userInput from description
            setSavedDiagram({''',
    },
    "SAVE-003": {
        "file": "/app/frontend/src/pages/DiagramRenderer.js",
        "description": "Save button stays disabled after save completes",
        "category": "Save/Load",
        "difficulty": "Medium",
        "points": 10,
        "time_estimate": "1.5 min",
        "original": '''      toast.success(savedDiagram?.id ? 'Diagram updated!' : 'Diagram saved!');
    } catch (err) {
      toast.error(err.message);
    } finally {
      setIsSaving(false);
    }''',
        "buggy": '''      toast.success(savedDiagram?.id ? 'Diagram updated!' : 'Diagram saved!');
    } catch (err) {
      toast.error(err.message);
    }
    // BUG: Missing finally block - isSaving never reset to false''',
    },
    "SAVE-004": {
        "file": "/app/frontend/src/pages/DiagramRenderer.js",
        "description": "Last saved timestamp doesn't update after saving",
        "category": "Save/Load",
        "difficulty": "Medium",
        "points": 10,
        "time_estimate": "2 min",
        "original": '''      setSavedDiagram({
        id: data.id,
        title: data.title,
        description: data.description,
        folder_id: data.folder_id,
        updated_at: data.updated_at
      });''',
        "buggy": '''      setSavedDiagram({
        id: data.id,
        title: data.title,
        description: data.description,
        folder_id: data.folder_id,
        updated_at: savedDiagram?.updated_at  // BUG: Using old timestamp instead of new one
      });''',
    },
    "SAVE-005": {
        "file": "/app/frontend/src/components/SaveDiagramModal.js",
        "description": "Title field doesn't clear after save - should reset form",
        "category": "Save/Load",
        "difficulty": "Easy",
        "points": 5,
        "time_estimate": "1 min",
        "original": '''    setError('');
    onSave({ 
      title: title.trim(), 
      description: description.trim(),
      folder_id: folderId || null
    });
    // Reset form after save
    if (!existingTitle) {
      setTitle('');
      setDescription('');
    }
  };''',
        "buggy": '''    setError('');
    onSave({ 
      title: title.trim(), 
      description: description.trim(),
      folder_id: folderId || null
    });
    // BUG: Form not reset after save
  };''',
    },
    "SAVE-006": {
        "file": "/app/backend/server.py",
        "description": "Save without title succeeds - should require title",
        "category": "Save/Load",
        "difficulty": "Easy",
        "points": 5,
        "time_estimate": "1.5 min",
        "original": '''class DiagramCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: str = Field(default="", max_length=1000)
    diagram_type: str
    diagram_code: str
    folder_id: str | None = None''',
        "buggy": '''class DiagramCreate(BaseModel):
    title: str = Field(default="", max_length=200)  # BUG: No min_length validation
    description: str = Field(default="", max_length=1000)
    diagram_type: str
    diagram_code: str
    folder_id: str | None = None''',
    },
    
    # ============== LIST/DISPLAY BUGS ==============
    "LIST-001": {
        "file": "/app/backend/server.py",
        "description": "My Diagrams shows everyone's diagrams - Missing user_id filter",
        "category": "List/Display",
        "difficulty": "Hard",
        "points": 15,
        "time_estimate": "4 min",
        "original": '''    # Filter by user_id to show only user's diagrams
    query_filter = {"user_id": current_user.user_id}''',
        "buggy": '''    # BUG: Missing user_id filter - shows all diagrams
    query_filter = {}''',
    },
    "LIST-002": {
        "file": "/app/frontend/src/components/DiagramCard.js",
        "description": "Delete removes wrong diagram - passing wrong diagram to handler",
        "category": "List/Display",
        "difficulty": "Medium",
        "points": 10,
        "time_estimate": "2.5 min",
        "original": '''  const handleDeleteClick = (e) => {
    e.stopPropagation(); // Prevent card click
    onDelete(diagram);
  };''',
        "buggy": '''  const handleDeleteClick = (e) => {
    e.stopPropagation(); // Prevent card click
    onDelete({ ...diagram, id: diagram.id + '_wrong' });  // BUG: Corrupted ID
  };''',
    },
    "LIST-003": {
        "file": "/app/backend/server.py",
        "description": "Diagram list sorted oldest first - should show newest first",
        "category": "List/Display",
        "difficulty": "Easy",
        "points": 5,
        "time_estimate": "1.5 min",
        "original": '''    # Sort by updated_at descending (newest first)
    sort_direction = -1''',
        "buggy": '''    # Sort by updated_at (BUG: ascending shows oldest first)
    sort_direction = 1''',
    },
    "LIST-004": {
        "file": "/app/frontend/src/pages/DiagramsList.js",
        "description": "Diagram count doesn't update after delete",
        "category": "List/Display",
        "difficulty": "Medium",
        "points": 10,
        "time_estimate": "2 min",
        "original": '''      // Remove from local state
      setDiagrams(prevDiagrams => prevDiagrams.filter(d => d.id !== deleteTarget.id));
      toast.success('Diagram deleted successfully');''',
        "buggy": '''      // Remove from local state - BUG: Not updating state correctly
      toast.success('Diagram deleted successfully');''',
    },
    "LIST-005": {
        "file": "/app/frontend/src/components/DiagramCard.js",
        "description": "Created date shows raw ISO format instead of readable date",
        "category": "List/Display",
        "difficulty": "Easy",
        "points": 5,
        "time_estimate": "1 min",
        "original": '''        <span className="flex items-center gap-1.5 text-xs text-slate-400">
          <Calendar className="w-3.5 h-3.5" />
          {formatDate(diagram.created_at)}
        </span>''',
        "buggy": '''        <span className="flex items-center gap-1.5 text-xs text-slate-400">
          <Calendar className="w-3.5 h-3.5" />
          {diagram.created_at}
        </span>''',
    },
    
    # ============== EXPORT BUGS ==============
    "EXPORT-001": {
        "file": "/app/frontend/src/pages/DiagramRenderer.js",
        "description": "Export filename always 'diagram.png' - should use diagram title",
        "category": "Export",
        "difficulty": "Easy",
        "points": 5,
        "time_estimate": "1 min",
        "original": '''  // Generate filename from diagram title or default
  const getExportFilename = (format) => {
    const title = savedDiagram?.title;
    if (title) {
      // Sanitize title for filename (remove special characters)
      const sanitizedTitle = title
        .toLowerCase()
        .replace(/[^a-z0-9]+/g, '-')
        .replace(/^-|-$/g, '');
      return `${sanitizedTitle}.${format}`;
    }
    return `diagram-${Date.now()}.${format}`;
  };''',
        "buggy": '''  // Generate filename from diagram title or default
  const getExportFilename = (format) => {
    // BUG: Always returns generic filename, ignores diagram title
    return `diagram.${format}`;
  };''',
    },
    "EXPORT-002": {
        "file": "/app/frontend/src/pages/DiagramRenderer.js",
        "description": "Export button loading spinner never clears",
        "category": "Export",
        "difficulty": "Medium",
        "points": 10,
        "time_estimate": "1.5 min",
        "original": '''    } catch (err) {
      toast.error(`Failed to export diagram: ${err.message}`);
      console.error('Export error:', err);
    } finally {
      setIsExporting(false);
    }
  };''',
        "buggy": '''    } catch (err) {
      toast.error(`Failed to export diagram: ${err.message}`);
      console.error('Export error:', err);
    }
    // BUG: Missing finally block - isExporting never reset to false
  };''',
    },
    "EXPORT-003": {
        "file": "/app/frontend/src/components/PreviewPanel.js",
        "description": "Export button not disabled during export - allows duplicate downloads",
        "category": "Export",
        "difficulty": "Easy",
        "points": 5,
        "time_estimate": "1 min",
        "original": '''                <DropdownMenu>
                  <DropdownMenuTrigger asChild>
                    <Button
                      size="sm"
                      disabled={isExporting}
                      className="bg-gradient-to-r from-blue-600 to-teal-600 hover:from-blue-700 hover:to-teal-700 text-white h-8 px-3 text-xs rounded-lg shadow-md disabled:opacity-50 disabled:cursor-not-allowed"
                      data-testid="export-button"
                    >''',
        "buggy": '''                <DropdownMenu>
                  <DropdownMenuTrigger asChild>
                    <Button
                      size="sm"
                      className="bg-gradient-to-r from-blue-600 to-teal-600 hover:from-blue-700 hover:to-teal-700 text-white h-8 px-3 text-xs rounded-lg shadow-md"
                      data-testid="export-button"
                    >''',
    },
    
    # ============== SEARCH BUGS ==============
    "SEARCH-001": {
        "file": "/app/frontend/src/pages/DiagramsList.js",
        "description": "Search is case-sensitive - should be case-insensitive",
        "category": "Search",
        "difficulty": "Easy",
        "points": 5,
        "time_estimate": "1 min",
        "original": '''      const query = debouncedSearchQuery.toLowerCase().trim();
      result = result.filter(diagram => 
        diagram.title.toLowerCase().includes(query) ||
        (diagram.description && diagram.description.toLowerCase().includes(query))
      );''',
        "buggy": '''      const query = debouncedSearchQuery.trim();  // BUG: case-sensitive
      result = result.filter(diagram => 
        diagram.title.includes(query) ||
        (diagram.description && diagram.description.includes(query))
      );''',
    },
    "SEARCH-002": {
        "file": "/app/frontend/src/pages/DiagramsList.js",
        "description": "Search ignores folder filter - shows results from all folders",
        "category": "Search",
        "difficulty": "Medium",
        "points": 10,
        "time_estimate": "2 min",
        "original": '''    // Filter by folder
    if (selectedFolderId === 'none') {
      result = result.filter(d => !d.folder_id);
    } else if (selectedFolderId) {
      result = result.filter(d => d.folder_id === selectedFolderId);
    }
    
    // Filter by search query
    if (debouncedSearchQuery.trim()) {''',
        "buggy": '''    // BUG: Only apply folder filter when not searching
    if (!debouncedSearchQuery.trim()) {
      if (selectedFolderId === 'none') {
        result = result.filter(d => !d.folder_id);
      } else if (selectedFolderId) {
        result = result.filter(d => d.folder_id === selectedFolderId);
      }
    }
    
    // Filter by search query
    if (debouncedSearchQuery.trim()) {''',
    },
    "SEARCH-003": {
        "file": "/app/frontend/src/pages/DiagramsList.js",
        "description": "Clear search button doesn't work - search state not cleared",
        "category": "Search",
        "difficulty": "Medium",
        "points": 10,
        "time_estimate": "1.5 min",
        "original": '''  // Clear search
  const handleClearSearch = () => {
    setSearchQuery('');
  };''',
        "buggy": '''  // Clear search - BUG: doesn't actually clear
  const handleClearSearch = () => {
    console.log('Clear search clicked');  // Missing setSearchQuery('')
  };''',
    },
    "SEARCH-004": {
        "file": "/app/frontend/src/pages/DiagramsList.js",
        "description": "Search input doesn't debounce - causes lag on every keystroke",
        "category": "Search",
        "difficulty": "Easy",
        "points": 5,
        "time_estimate": "1.5 min",
        "original": '''  // Search state
  const [searchQuery, setSearchQuery] = useState('');
  const debouncedSearchQuery = useDebounce(searchQuery, 300);''',
        "buggy": '''  // Search state - BUG: not using debounce
  const [searchQuery, setSearchQuery] = useState('');
  const debouncedSearchQuery = searchQuery;  // Should use useDebounce''',
    },
}


def read_file(filepath: str) -> str:
    """Read file content."""
    with open(filepath, 'r') as f:
        return f.read()


def write_file(filepath: str, content: str) -> None:
    """Write content to file."""
    with open(filepath, 'w') as f:
        f.write(content)


def inject_bug(bug_id: str) -> Tuple[bool, str]:
    """
    Inject a single bug into the codebase.
    Returns (success, message).
    """
    if bug_id not in BUGS:
        return False, f"Bug {bug_id} not found"
    
    bug = BUGS[bug_id]
    filepath = bug["file"]
    
    if not os.path.exists(filepath):
        return False, f"File not found: {filepath}"
    
    content = read_file(filepath)
    
    # Check if bug is already injected
    if bug["buggy"] in content:
        return True, f"{bug_id}: Already injected"
    
    # Check if original code exists
    if bug["original"] not in content:
        return False, f"{bug_id}: Original code not found (may already be modified)"
    
    # Inject the bug
    new_content = content.replace(bug["original"], bug["buggy"])
    write_file(filepath, new_content)
    
    return True, f"{bug_id}: Injected successfully"


def inject_all_bugs() -> List[Tuple[str, bool, str]]:
    """Inject all bugs. Returns list of (bug_id, success, message)."""
    results = []
    for bug_id in BUGS:
        success, message = inject_bug(bug_id)
        results.append((bug_id, success, message))
    return results


def list_bugs() -> None:
    """Print all available bugs."""
    print("\n" + "="*70)
    print("AVAILABLE BUGS FOR INJECTION")
    print("="*70)
    
    total_points = 0
    for bug_id, bug in BUGS.items():
        points = bug.get('points', 5)
        total_points += points
        print(f"\n[{bug_id}]")
        print(f"  Category:    {bug['category']}")
        print(f"  Difficulty:  {bug['difficulty']}")
        print(f"  Points:      {points}")
        print(f"  Time Est:    {bug['time_estimate']}")
        print(f"  File:        {bug['file']}")
        print(f"  Description: {bug['description']}")
    
    print("\n" + "="*70)
    print(f"Total: {len(BUGS)} bugs | {total_points} points")
    print("="*70 + "\n")


def check_bug_status(bug_id: str) -> str:
    """Check if a bug is currently injected."""
    if bug_id not in BUGS:
        return "NOT_FOUND"
    
    bug = BUGS[bug_id]
    filepath = bug["file"]
    
    if not os.path.exists(filepath):
        return "FILE_MISSING"
    
    content = read_file(filepath)
    
    if bug["buggy"] in content:
        return "INJECTED"
    elif bug["original"] in content:
        return "FIXED"
    else:
        return "UNKNOWN"


def main():
    parser = argparse.ArgumentParser(description="Bug Injector for Developer Assessment")
    parser.add_argument("--list", action="store_true", help="List all available bugs")
    parser.add_argument("--bug", type=str, help="Inject specific bug by ID (e.g., AUTH-001)")
    parser.add_argument("--status", action="store_true", help="Show current status of all bugs")
    parser.add_argument("--category", type=str, help="Inject bugs from specific category only")
    
    args = parser.parse_args()
    
    if args.list:
        list_bugs()
        return
    
    if args.status:
        print("\n" + "="*50)
        print("BUG STATUS")
        print("="*50)
        for bug_id in BUGS:
            status = check_bug_status(bug_id)
            status_icon = "🐛" if status == "INJECTED" else "✅" if status == "FIXED" else "❓"
            print(f"{status_icon} {bug_id}: {status}")
        print("="*50 + "\n")
        return
    
    if args.bug:
        success, message = inject_bug(args.bug)
        icon = "✅" if success else "❌"
        print(f"{icon} {message}")
        return
    
    if args.category:
        print(f"\n" + "="*50)
        print(f"INJECTING {args.category.upper()} BUGS")
        print("="*50)
        
        success_count = 0
        total_count = 0
        for bug_id, bug in BUGS.items():
            if bug["category"].lower() == args.category.lower():
                total_count += 1
                success, message = inject_bug(bug_id)
                icon = "✅" if success else "❌"
                print(f"{icon} {message}")
                if success:
                    success_count += 1
        
        print("="*50)
        print(f"Injected: {success_count}/{total_count} bugs")
        print("="*50 + "\n")
        return
    
    # Default: inject all bugs
    print("\n" + "="*50)
    print("INJECTING ALL BUGS")
    print("="*50)
    
    results = inject_all_bugs()
    success_count = 0
    
    for bug_id, success, message in results:
        icon = "✅" if success else "❌"
        print(f"{icon} {message}")
        if success:
            success_count += 1
    
    print("="*50)
    print(f"Injected: {success_count}/{len(BUGS)} bugs")
    print("="*50 + "\n")


if __name__ == "__main__":
    main()
