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

# Bug definitions with flexible evaluation
# - "original" and "buggy" are used for inject/fix operations
# - "check_fixed" is a function that returns True if the bug is logically fixed
# - "check_buggy" is a function that returns True if the bug is present

BUGS: Dict[str, Dict] = {
    # ============== AUTHENTICATION BUGS ==============
    "AUTH-001": {
        "file": "/app/backend/server.py",
        "description": "Email case-sensitive login - Login should be case-insensitive",
        "category": "Authentication",
        "difficulty": "Easy",
        "points": 5,
        "time_estimate": "1 min",
        "hint": "Look for the login endpoint and check if email is normalized to lowercase",
        "original": '''    # Find user by email
    user_doc = await db.users.find_one({"email": credentials.email.lower()})''',
        "buggy": '''    # Find user by email
    # FIXME: Users report they can't login when using different letter casing
    user_doc = await db.users.find_one({"email": credentials.email})''',
        # Flexible check: is .lower() used on credentials.email in login?
        "fix_check": lambda content: bool(re.search(r'credentials\.email\.lower\(\)', content)),
        "bug_check": lambda content: bool(re.search(r'find_one\(\{["\']email["\']:\s*credentials\.email\}', content)),
    },
    "AUTH-002": {
        "file": "/app/backend/server.py",
        "description": "Duplicate email registration allowed - Should check for existing email",
        "category": "Authentication",
        "difficulty": "Easy",
        "points": 5,
        "time_estimate": "2 min",
        "hint": "Look for signup endpoint - is there a check for existing user before creating?",
        "original": '''    # Check if user already exists
    existing_user = await db.users.find_one({"email": user_data.email.lower()})
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )''',
        "buggy": '''    # TODO: Re-enable duplicate email check - users can register same email multiple times!
    # existing_user = await db.users.find_one({"email": user_data.email})
    # if existing_user:
    #     raise HTTPException(
    #         status_code=status.HTTP_400_BAD_REQUEST,
    #         detail="Email already registered"
    #     )''',
        # Flexible check: is there an active check for existing user?
        "fix_check": lambda content: bool(re.search(r'existing_user\s*=\s*await\s+db\.users\.find_one.*email.*\n\s*if\s+existing_user:', content, re.MULTILINE)),
        "bug_check": lambda content: bool(re.search(r'#\s*existing_user\s*=|#\s*if\s+existing_user:', content)),
    },
    "AUTH-003": {
        "file": "/app/frontend/src/context/AuthContext.js",
        "description": "Logout doesn't clear token from localStorage",
        "category": "Authentication",
        "difficulty": "Easy",
        "points": 5,
        "time_estimate": "1 min",
        "hint": "Check the logout function - does it remove the token from localStorage?",
        "original": '''  const logout = () => {
    localStorage.removeItem('token');
    setToken(null);
    setUser(null);
  };''',
        "buggy": '''  const logout = () => {
    // FIXME: Users report staying logged in after logout - token persists somewhere
    setToken(null);
    setUser(null);
  };''',
        # Flexible check: does logout function call localStorage.removeItem?
        "fix_check": lambda content: bool(re.search(r'logout\s*=\s*\([^)]*\)\s*=>\s*\{[^}]*localStorage\.removeItem\s*\(\s*[\'"]token[\'"]\s*\)', content, re.DOTALL)),
        "bug_check": lambda content: bool(re.search(r'logout\s*=\s*\([^)]*\)\s*=>\s*\{[^}]*setToken\(null\)', content, re.DOTALL)) and not bool(re.search(r'localStorage\.removeItem\s*\(\s*[\'"]token[\'"]\s*\)', content)),
    },
    "AUTH-004": {
        "file": "/app/backend/server.py",
        "description": "Password minimum length not enforced - Should require 6+ characters",
        "category": "Authentication",
        "difficulty": "Easy",
        "points": 5,
        "time_estimate": "1 min",
        "hint": "Check signup endpoint - is password length validated?",
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
    # TODO: Add password length validation - docstring says 6 chars minimum but it's not enforced!
    
    # Check if user already exists''',
        # Flexible check: is there password length validation?
        "fix_check": lambda content: bool(re.search(r'len\s*\(\s*user_data\.password\s*\)\s*<\s*\d+', content)) or bool(re.search(r'password.*min_length', content)),
        "bug_check": lambda content: not bool(re.search(r'len\s*\(\s*user_data\.password\s*\)\s*<\s*\d+', content)) and bool(re.search(r'async def signup', content)),
    },
    
    # ============== SAVE/LOAD BUGS ==============
    "SAVE-001": {
        "file": "/app/backend/server.py",
        "description": "Save creates duplicate entries - Should update existing diagram with same title",
        "category": "Save/Load",
        "difficulty": "Hard",
        "points": 15,
        "time_estimate": "4 min",
        "hint": "In POST /diagrams, check if a diagram with same title exists before creating new one",
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
    # FIXME: Users report duplicate diagrams when saving with same title - should update instead
    
    # Validate folder_id if provided''',
        # Flexible check: is there a check for existing diagram before insert?
        "fix_check": lambda content: bool(re.search(r'existing_diagram\s*=\s*await\s+db\.diagrams\.find_one.*title.*diagram_data\.title', content, re.DOTALL)) and bool(re.search(r'if\s+existing_diagram:', content)),
        "bug_check": lambda content: bool(re.search(r'Duplicate check disabled|#\s*existing_diagram', content)),
    },
    "SAVE-002": {
        "file": "/app/frontend/src/pages/DiagramRenderer.js",
        "description": "Load diagram doesn't populate textarea - diagram code not loaded properly",
        "category": "Save/Load",
        "difficulty": "Medium",
        "points": 10,
        "time_estimate": "2 min",
        "hint": "When loading a diagram, is setUserInput called with the description?",
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
            // TODO: The textarea is empty when loading a saved diagram - description not populated
            setSavedDiagram({''',
        # Flexible check: is setUserInput called with description when loading?
        "fix_check": lambda content: bool(re.search(r'setUserInput\s*\(\s*data\.description', content)),
        "bug_check": lambda content: bool(re.search(r'setGeneratedCode\(data\.diagram_code\)', content)) and not bool(re.search(r'setUserInput\s*\(\s*data\.description', content)),
    },
    "SAVE-003": {
        "file": "/app/frontend/src/pages/DiagramRenderer.js",
        "description": "Save button stays disabled after save completes",
        "category": "Save/Load",
        "difficulty": "Medium",
        "points": 10,
        "time_estimate": "1.5 min",
        "hint": "Check if setIsSaving(false) is called in a finally block",
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
    // FIXME: Save button stays disabled forever after first save - state not cleaned up''',
        # Flexible check: is there a finally block with setIsSaving(false)?
        "fix_check": lambda content: bool(re.search(r'finally\s*\{[^}]*setIsSaving\s*\(\s*false\s*\)', content, re.DOTALL)),
        "bug_check": lambda content: bool(re.search(r'catch\s*\([^)]*\)\s*\{[^}]*\}\s*\n\s*//|catch\s*\([^)]*\)\s*\{[^}]*\}\s*$', content, re.MULTILINE)) and not bool(re.search(r'finally\s*\{[^}]*setIsSaving\s*\(\s*false\s*\)', content, re.DOTALL)),
    },
    "SAVE-004": {
        "file": "/app/frontend/src/pages/DiagramRenderer.js",
        "description": "Last saved timestamp doesn't update after saving",
        "category": "Save/Load",
        "difficulty": "Medium",
        "points": 10,
        "time_estimate": "2 min",
        "hint": "Check if updated_at is set from API response data, not from old state",
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
        updated_at: savedDiagram?.updated_at  // FIXME: "Last saved" time never changes after re-saving
      });''',
        # Flexible check: is updated_at set from data.updated_at?
        "fix_check": lambda content: bool(re.search(r'updated_at:\s*data\.updated_at', content)),
        "bug_check": lambda content: bool(re.search(r'updated_at:\s*savedDiagram\?\.updated_at', content)),
    },
    "SAVE-005": {
        "file": "/app/frontend/src/components/SaveDiagramModal.js",
        "description": "Title field doesn't clear after save - should reset form",
        "category": "Save/Load",
        "difficulty": "Easy",
        "points": 5,
        "time_estimate": "1 min",
        "hint": "After onSave is called, should the form fields be reset?",
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
    // TODO: Title field shows old value when opening modal for new diagram
  };''',
        # Flexible check: is setTitle('') called after onSave?
        "fix_check": lambda content: bool(re.search(r'onSave\s*\([^)]*\)[^;]*;[^}]*setTitle\s*\(\s*[\'"][\'"]', content, re.DOTALL)),
        "bug_check": lambda content: bool(re.search(r'onSave\s*\([^)]*\)', content)) and not bool(re.search(r'onSave\s*\([^)]*\)[^;]*;[^}]*setTitle\s*\(\s*[\'"][\'"]', content, re.DOTALL)),
    },
    
    # ============== LIST/DISPLAY BUGS ==============
    "LIST-001": {
        "file": "/app/backend/server.py",
        "description": "My Diagrams shows everyone's diagrams - Missing user_id filter",
        "category": "List/Display",
        "difficulty": "Hard",
        "points": 15,
        "time_estimate": "4 min",
        "hint": "In GET /diagrams, is the query filtering by user_id?",
        "original": '''    # Filter by user_id to show only user's diagrams
    query_filter = {"user_id": current_user.user_id}''',
        "buggy": '''    # FIXME: Users can see other users' diagrams! Security issue - needs filtering
    query_filter = {}''',
        # Flexible check: is user_id in the query filter?
        "fix_check": lambda content: bool(re.search(r'query_filter\s*=\s*\{[^}]*["\']?user_id["\']?\s*:', content)) or bool(re.search(r'find\s*\(\s*\{[^}]*user_id[^}]*current_user', content)),
        "bug_check": lambda content: bool(re.search(r'query_filter\s*=\s*\{\s*\}', content)),
    },
    "LIST-002": {
        "file": "/app/frontend/src/components/DiagramCard.js",
        "description": "Delete removes wrong diagram - passing wrong diagram to handler",
        "category": "List/Display",
        "difficulty": "Medium",
        "points": 10,
        "time_estimate": "2.5 min",
        "hint": "Check handleDeleteClick - is the correct diagram being passed?",
        "original": '''  const handleDeleteClick = (e) => {
    e.stopPropagation(); // Prevent card click
    onDelete(diagram);
  };''',
        "buggy": '''  const handleDeleteClick = (e) => {
    e.stopPropagation(); // Prevent card click
    // FIXME: Wrong diagram gets deleted when clicking delete button
    onDelete({ ...diagram, id: diagram.id + '_wrong' });
  };''',
        # Flexible check: is onDelete called with just diagram (not corrupted)?
        "fix_check": lambda content: bool(re.search(r'onDelete\s*\(\s*diagram\s*\)', content)),
        "bug_check": lambda content: bool(re.search(r'onDelete\s*\(\s*\{[^}]*_wrong', content)) or bool(re.search(r'onDelete\s*\(\s*\{[^}]*\+', content)),
    },
    "LIST-004": {
        "file": "/app/frontend/src/pages/DiagramsList.js",
        "description": "Diagram count doesn't update after delete",
        "category": "List/Display",
        "difficulty": "Medium",
        "points": 10,
        "time_estimate": "2 min",
        "hint": "After delete API call, is the local diagrams state being updated?",
        "original": '''      // Remove from local state
      setDiagrams(prevDiagrams => prevDiagrams.filter(d => d.id !== deleteTarget.id));
      toast.success('Diagram deleted successfully');''',
        "buggy": '''      // FIXME: Diagram count in sidebar doesn't decrease after deletion
      toast.success('Diagram deleted successfully');''',
        # Flexible check: is setDiagrams called with filter after delete?
        "fix_check": lambda content: bool(re.search(r'setDiagrams\s*\([^)]*filter\s*\(', content)),
        "bug_check": lambda content: bool(re.search(r'toast\.success.*[Dd]eleted', content)) and not bool(re.search(r'setDiagrams\s*\([^)]*filter', content)),
    },
    "LIST-005": {
        "file": "/app/frontend/src/components/DiagramCard.js",
        "description": "Created date shows raw ISO format instead of readable date",
        "category": "List/Display",
        "difficulty": "Easy",
        "points": 5,
        "time_estimate": "1 min",
        "hint": "Is the date being formatted before display?",
        "original": '''        <span className="flex items-center gap-1.5 text-xs text-slate-400">
          <Calendar className="w-3.5 h-3.5" />
          {formatDate(diagram.created_at)}
        </span>''',
        "buggy": '''        <span className="flex items-center gap-1.5 text-xs text-slate-400">
          <Calendar className="w-3.5 h-3.5" />
          {/* TODO: Date displays as ugly ISO string like "2024-01-15T10:30:00.000Z" */}
          {diagram.created_at}
        </span>''',
        # Flexible check: is formatDate or toLocaleDateString used?
        "fix_check": lambda content: bool(re.search(r'formatDate\s*\(\s*diagram\.created_at\s*\)', content)) or bool(re.search(r'diagram\.created_at.*toLocale', content)) or bool(re.search(r'new Date\s*\(\s*diagram\.created_at\s*\)', content)),
        "bug_check": lambda content: bool(re.search(r'\{\s*diagram\.created_at\s*\}', content)) and not bool(re.search(r'formatDate|toLocale|new Date', content)),
    },
    
    # ============== EXPORT BUGS ==============
    "EXPORT-001": {
        "file": "/app/frontend/src/pages/DiagramRenderer.js",
        "description": "Export filename always 'diagram.png' - should use diagram title",
        "category": "Export",
        "difficulty": "Easy",
        "points": 5,
        "time_estimate": "1 min",
        "hint": "Check getExportFilename - is the diagram title being used?",
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
    // TODO: Downloaded files all named "diagram.png" - should use actual diagram title
    return `diagram.${format}`;
  };''',
        # Flexible check: is savedDiagram.title or title used in filename?
        "fix_check": lambda content: bool(re.search(r'getExportFilename[^}]*savedDiagram\?*\.title|getExportFilename[^}]*title[^}]*sanitize|getExportFilename[^}]*title[^}]*replace', content, re.DOTALL)),
        "bug_check": lambda content: bool(re.search(r'getExportFilename[^}]*return\s*[`\'"]diagram\.', content, re.DOTALL)) and not bool(re.search(r'savedDiagram\?*\.title', content)),
    },
    "EXPORT-002": {
        "file": "/app/frontend/src/pages/DiagramRenderer.js",
        "description": "Export button loading spinner never clears",
        "category": "Export",
        "difficulty": "Medium",
        "points": 10,
        "time_estimate": "1.5 min",
        "hint": "Is setIsExporting(false) called in a finally block?",
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
    // FIXME: Export button shows spinner forever after export fails
  };''',
        # Flexible check: is there a finally with setIsExporting(false)?
        "fix_check": lambda content: bool(re.search(r'finally\s*\{[^}]*setIsExporting\s*\(\s*false\s*\)', content, re.DOTALL)),
        "bug_check": lambda content: bool(re.search(r'setIsExporting\s*\(\s*true\s*\)', content)) and not bool(re.search(r'finally\s*\{[^}]*setIsExporting\s*\(\s*false\s*\)', content, re.DOTALL)),
    },
    "EXPORT-003": {
        "file": "/app/frontend/src/components/PreviewPanel.js",
        "description": "Export button not disabled during export - allows duplicate downloads",
        "category": "Export",
        "difficulty": "Easy",
        "points": 5,
        "time_estimate": "1 min",
        "hint": "Is the export button disabled when isExporting is true?",
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
                    {/* TODO: Users can spam-click export and download multiple copies */}
                    <Button
                      size="sm"
                      className="bg-gradient-to-r from-blue-600 to-teal-600 hover:from-blue-700 hover:to-teal-700 text-white h-8 px-3 text-xs rounded-lg shadow-md"
                      data-testid="export-button"
                    >''',
        # Flexible check: is disabled={isExporting} on the export button?
        "fix_check": lambda content: bool(re.search(r'data-testid=["\']export-button["\'][^>]*disabled\s*=\s*\{?\s*isExporting|disabled\s*=\s*\{?\s*isExporting[^>]*data-testid=["\']export-button["\']', content, re.DOTALL)),
        "bug_check": lambda content: bool(re.search(r'data-testid=["\']export-button["\']', content)) and not bool(re.search(r'disabled\s*=\s*\{?\s*isExporting', content)),
    },
    
    # ============== SEARCH BUGS ==============
    "SEARCH-001": {
        "file": "/app/frontend/src/pages/DiagramsList.js",
        "description": "Search is case-sensitive - should be case-insensitive",
        "category": "Search",
        "difficulty": "Easy",
        "points": 5,
        "time_estimate": "1 min",
        "hint": "Is toLowerCase() used when comparing search query with titles?",
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
        # Flexible check: is toLowerCase used in search filtering?
        "fix_check": lambda content: bool(re.search(r'\.toLowerCase\(\).*\.includes\(.*query|query.*\.toLowerCase\(\)', content)),
        "bug_check": lambda content: bool(re.search(r'\.filter\([^)]*diagram\.title\.includes\(query\)', content)) and not bool(re.search(r'toLowerCase', content)),
    },
    "SEARCH-002": {
        "file": "/app/frontend/src/pages/DiagramsList.js",
        "description": "Search ignores folder filter - shows results from all folders",
        "category": "Search",
        "difficulty": "Medium",
        "points": 10,
        "time_estimate": "2 min",
        "hint": "Is folder filtering applied regardless of search query?",
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
        # Flexible check: is folder filter NOT wrapped in !debouncedSearchQuery check?
        "fix_check": lambda content: bool(re.search(r'if\s*\(\s*selectedFolderId\s*===\s*[\'"]none[\'"]\s*\)', content)) and not bool(re.search(r'if\s*\(\s*!debouncedSearchQuery', content)),
        "bug_check": lambda content: bool(re.search(r'if\s*\(\s*!debouncedSearchQuery\.trim\(\)\s*\)\s*\{[^}]*selectedFolderId', content, re.DOTALL)),
    },
    "SEARCH-003": {
        "file": "/app/frontend/src/pages/DiagramsList.js",
        "description": "Clear search button doesn't work - search state not cleared",
        "category": "Search",
        "difficulty": "Medium",
        "points": 10,
        "time_estimate": "1.5 min",
        "hint": "Does handleClearSearch actually call setSearchQuery('')?",
        "original": '''  // Clear search
  const handleClearSearch = () => {
    setSearchQuery('');
  };''',
        "buggy": '''  // Clear search - BUG: doesn't actually clear
  const handleClearSearch = () => {
    console.log('Clear search clicked');  // Missing setSearchQuery('')
  };''',
        # Flexible check: does handleClearSearch call setSearchQuery('') within its body?
        "fix_check": lambda content: bool(re.search(r'handleClearSearch\s*=\s*\([^)]*\)\s*=>\s*\{[^}]*setSearchQuery\s*\(\s*[\'"][\'"]', content, re.DOTALL)),
        "bug_check": lambda content: bool(re.search(r'handleClearSearch\s*=\s*\([^)]*\)\s*=>\s*\{[^}]*console\.log', content, re.DOTALL)) or (bool(re.search(r'handleClearSearch', content)) and not bool(re.search(r'handleClearSearch\s*=\s*\([^)]*\)\s*=>\s*\{[^}]*setSearchQuery\s*\(\s*[\'"][\'"]', content, re.DOTALL))),
    },
    "SEARCH-004": {
        "file": "/app/frontend/src/pages/DiagramsList.js",
        "description": "Search input doesn't debounce - causes lag on every keystroke",
        "category": "Search",
        "difficulty": "Easy",
        "points": 5,
        "time_estimate": "1.5 min",
        "hint": "Is useDebounce being used for the search query?",
        "original": '''  // Search state
  const [searchQuery, setSearchQuery] = useState('');
  const debouncedSearchQuery = useDebounce(searchQuery, 300);''',
        "buggy": '''  // Search state - BUG: not using debounce
  const [searchQuery, setSearchQuery] = useState('');
  const debouncedSearchQuery = searchQuery;  // Should use useDebounce''',
        # Flexible check: is useDebounce used?
        "fix_check": lambda content: bool(re.search(r'debouncedSearchQuery\s*=\s*useDebounce\s*\(', content)),
        "bug_check": lambda content: bool(re.search(r'debouncedSearchQuery\s*=\s*searchQuery\s*;', content)),
    },
    
    # ============== FOLDER BUGS ==============
    "FOLDER-001": {
        "file": "/app/backend/server.py",
        "description": "Folder dropdown shows all users' folders - Missing user_id filter",
        "category": "Folders",
        "difficulty": "Medium",
        "points": 10,
        "time_estimate": "2 min",
        "hint": "In GET /folders, is the query filtering by user_id?",
        "original": '''@api_router.get("/folders", response_model=FolderListResponse)
async def get_user_folders(current_user: TokenData = Depends(get_current_user)):
    """
    Get all folders for the authenticated user.
    """
    folders = await db.folders.find(
        {"user_id": current_user.user_id},
        {"_id": 0}
    ).sort("name", 1).to_list(100)''',
        "buggy": '''@api_router.get("/folders", response_model=FolderListResponse)
async def get_user_folders(current_user: TokenData = Depends(get_current_user)):
    """
    Get all folders for the authenticated user.
    """
    # BUG: Missing user_id filter - shows all users' folders
    folders = await db.folders.find(
        {},
        {"_id": 0}
    ).sort("name", 1).to_list(100)''',
        # Flexible check: is user_id filter in folders.find?
        "fix_check": lambda content: bool(re.search(r'db\.folders\.find\s*\(\s*\{[^}]*user_id', content)),
        "bug_check": lambda content: bool(re.search(r'db\.folders\.find\s*\(\s*\{\s*\}', content)),
    },
    "FOLDER-002": {
        "file": "/app/frontend/src/pages/DiagramRenderer.js",
        "description": "Folder selection not saved with diagram - folder_id not included in save",
        "category": "Folders",
        "difficulty": "Medium",
        "points": 10,
        "time_estimate": "2 min",
        "hint": "When saving diagram, is folder_id included in the request body?",
        "original": '''      const diagramData = {
        title,
        description,
        diagram_type: diagramType,
        diagram_code: generatedCode,
        folder_id: folder_id
      };''',
        "buggy": '''      const diagramData = {
        title,
        description,
        diagram_type: diagramType,
        diagram_code: generatedCode,
        // BUG: folder_id not included in save
      };''',
        # Flexible check: is folder_id in diagramData?
        "fix_check": lambda content: bool(re.search(r'diagramData\s*=\s*\{[^}]*folder_id\s*:', content, re.DOTALL)),
        "bug_check": lambda content: bool(re.search(r'diagramData\s*=\s*\{[^}]*diagram_code', content, re.DOTALL)) and not bool(re.search(r'diagramData\s*=\s*\{[^}]*folder_id\s*:', content, re.DOTALL)),
    },
    "FOLDER-003": {
        "file": "/app/frontend/src/components/CreateFolderModal.js",
        "description": "Create folder with empty name succeeds - missing validation",
        "category": "Folders",
        "difficulty": "Easy",
        "points": 5,
        "time_estimate": "1 min",
        "hint": "Is there validation to prevent empty folder names?",
        "original": '''  const handleSubmit = (e) => {
    e.preventDefault();
    
    if (!name.trim()) {
      setError('Folder name is required');
      return;
    }
    
    if (name.length > 100) {
      setError('Folder name must be less than 100 characters');
      return;
    }
    
    setError('');
    onCreate(name.trim());
  };''',
        "buggy": '''  const handleSubmit = (e) => {
    e.preventDefault();
    
    // BUG: No validation - allows empty folder names
    
    setError('');
    onCreate(name.trim());
  };''',
        # Flexible check: is there validation for empty name?
        "fix_check": lambda content: bool(re.search(r'!name\.trim\(\)|name\.trim\(\)\s*===\s*[\'"][\'"]|name\s*===\s*[\'"][\'"]', content)),
        "bug_check": lambda content: bool(re.search(r'onCreate\s*\(', content)) and not bool(re.search(r'if\s*\(\s*!name\.trim\(\)|if\s*\(\s*name\.trim\(\)\s*===', content)),
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
    """Inject a single bug into the codebase."""
    if bug_id not in BUGS:
        return False, f"Bug {bug_id} not found"
    
    bug = BUGS[bug_id]
    filepath = bug["file"]
    
    if not os.path.exists(filepath):
        return False, f"File not found: {filepath}"
    
    content = read_file(filepath)
    
    if bug["buggy"] in content:
        return True, f"{bug_id}: Already injected"
    
    if bug["original"] not in content:
        return False, f"{bug_id}: Original code not found (may already be modified)"
    
    new_content = content.replace(bug["original"], bug["buggy"])
    write_file(filepath, new_content)
    
    return True, f"{bug_id}: Injected successfully"


def inject_all_bugs() -> List[Tuple[str, bool, str]]:
    """Inject all bugs."""
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
        if "hint" in bug:
            print(f"  Hint:        {bug['hint']}")
    
    print("\n" + "="*70)
    print(f"Total: {len(BUGS)} bugs | {total_points} points")
    print("="*70 + "\n")


def check_bug_status(bug_id: str) -> str:
    """Check if a bug is fixed using flexible logic-based checking."""
    if bug_id not in BUGS:
        return "NOT_FOUND"
    
    bug = BUGS[bug_id]
    filepath = bug["file"]
    
    if not os.path.exists(filepath):
        return "FILE_MISSING"
    
    content = read_file(filepath)
    
    # Use flexible checking if available
    if "fix_check" in bug and "bug_check" in bug:
        is_fixed = bug["fix_check"](content)
        is_buggy = bug["bug_check"](content)
        
        if is_fixed and not is_buggy:
            return "FIXED"
        elif is_buggy:
            return "INJECTED"
        elif is_fixed:
            return "FIXED"
        else:
            # Fallback to exact matching
            if bug["buggy"] in content:
                return "INJECTED"
            elif bug["original"] in content:
                return "FIXED"
            return "UNKNOWN"
    else:
        # Fallback to exact string matching
        if bug["buggy"] in content:
            return "INJECTED"
        elif bug["original"] in content:
            return "FIXED"
        return "UNKNOWN"


def main():
    parser = argparse.ArgumentParser(description="Bug Injector for Developer Assessment")
    parser.add_argument("--list", action="store_true", help="List all available bugs")
    parser.add_argument("--bug", type=str, help="Inject specific bug by ID")
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
