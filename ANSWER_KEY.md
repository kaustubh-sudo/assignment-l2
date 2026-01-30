# Answer Key - Bug Fixes (CONFIDENTIAL)

> ⚠️ **FOR ASSESSORS ONLY** - Do not share with candidates

---

## Summary

| Bug ID | Category | Difficulty | Points | File |
|--------|----------|-----------|--------|------|
| AUTH-001 | Authentication | Easy | 5 | server.py |
| AUTH-002 | Authentication | Easy | 5 | server.py |
| AUTH-003 | Authentication | Easy | 5 | AuthContext.js |
| AUTH-004 | Authentication | Easy | 5 | server.py |
| SAVE-001 | Save/Load | Hard | 15 | server.py |
| SAVE-002 | Save/Load | Medium | 10 | DiagramRenderer.js |
| SAVE-003 | Save/Load | Medium | 10 | DiagramRenderer.js |
| SAVE-004 | Save/Load | Medium | 10 | DiagramRenderer.js |
| SAVE-005 | Save/Load | Easy | 5 | SaveDiagramModal.js |
| SAVE-006 | Save/Load | Easy | 5 | server.py |
| **Total** | | | **70** | |

---

## AUTH-001: Email Case-Sensitive Login

### Problem
The login endpoint performs a case-sensitive email lookup.

### File
`/app/backend/server.py` - Line ~194

### Buggy Code
```python
    # Find user by email
    user_doc = await db.users.find_one({"email": credentials.email})
```

### Fixed Code
```python
    # Find user by email
    user_doc = await db.users.find_one({"email": credentials.email.lower()})
```

---

## AUTH-002: Duplicate Email Registration Allowed

### Problem
The duplicate email check is commented out.

### File
`/app/backend/server.py` - Line ~161-167

### Buggy Code
```python
    # Check if user already exists - DISABLED FOR TESTING
    # existing_user = await db.users.find_one({"email": user_data.email})
    # if existing_user:
    #     raise HTTPException(
    #         status_code=status.HTTP_400_BAD_REQUEST,
    #         detail="Email already registered"
    #     )
```

### Fixed Code
```python
    # Check if user already exists
    existing_user = await db.users.find_one({"email": user_data.email.lower()})
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
```

---

## AUTH-003: Logout Doesn't Clear Token

### Problem
The logout function doesn't remove token from localStorage.

### File
`/app/frontend/src/context/AuthContext.js` - Line ~113-117

### Buggy Code
```javascript
  const logout = () => {
    // Token removal disabled
    setToken(null);
    setUser(null);
  };
```

### Fixed Code
```javascript
  const logout = () => {
    localStorage.removeItem('token');
    setToken(null);
    setUser(null);
  };
```

---

## AUTH-004: Password Minimum Length Not Enforced

### Problem
No server-side validation for password length.

### File
`/app/backend/server.py` - signup endpoint

### Buggy Code
```python
async def signup(user_data: UserCreate):
    """..."""
    # Password validation disabled for testing
    
    # Check if user already exists
```

### Fixed Code
```python
async def signup(user_data: UserCreate):
    """..."""
    # Validate password length
    if len(user_data.password) < 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 6 characters"
        )
    
    # Check if user already exists
```

---

## SAVE-001: Save Creates Duplicate Entries

### Problem
No check for existing diagram with same title before insert.

### File
`/app/backend/server.py` - POST /api/diagrams endpoint

### Buggy Code
```python
async def create_diagram(...):
    """..."""
    # Duplicate check disabled - allows multiple diagrams with same title
    
    # Validate folder_id if provided
```

### Fixed Code
```python
async def create_diagram(...):
    """..."""
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
        # ... return updated diagram
    
    # Validate folder_id if provided
```

---

## SAVE-002: Load Diagram Doesn't Populate Description

### Problem
When loading a diagram, the description/userInput is not set.

### File
`/app/frontend/src/pages/DiagramRenderer.js` - fetchDiagram function

### Buggy Code
```javascript
          if (response.ok) {
            const data = await response.json();
            setDiagramType(data.diagram_type);
            setGeneratedCode(data.diagram_code);
            // BUG: Not setting userInput from description
            setSavedDiagram({
```

### Fixed Code
```javascript
          if (response.ok) {
            const data = await response.json();
            setDiagramType(data.diagram_type);
            setGeneratedCode(data.diagram_code);
            setUserInput(data.description || '');
            setSavedDiagram({
```

---

## SAVE-003: Save Button Stays Disabled

### Problem
Missing `finally` block to reset `isSaving` state.

### File
`/app/frontend/src/pages/DiagramRenderer.js` - handleSaveDiagram function

### Buggy Code
```javascript
      toast.success(savedDiagram?.id ? 'Diagram updated!' : 'Diagram saved!');
    } catch (err) {
      toast.error(err.message);
    }
    // BUG: Missing finally block - isSaving never reset to false
```

### Fixed Code
```javascript
      toast.success(savedDiagram?.id ? 'Diagram updated!' : 'Diagram saved!');
    } catch (err) {
      toast.error(err.message);
    } finally {
      setIsSaving(false);
    }
```

---

## SAVE-004: "Last Saved" Timestamp Doesn't Update

### Problem
Using old timestamp instead of new one from API response.

### File
`/app/frontend/src/pages/DiagramRenderer.js` - handleSaveDiagram function

### Buggy Code
```javascript
      setSavedDiagram({
        id: data.id,
        title: data.title,
        description: data.description,
        folder_id: data.folder_id,
        updated_at: savedDiagram?.updated_at  // BUG: Using old timestamp
      });
```

### Fixed Code
```javascript
      setSavedDiagram({
        id: data.id,
        title: data.title,
        description: data.description,
        folder_id: data.folder_id,
        updated_at: data.updated_at
      });
```

---

## SAVE-005: Title Field Doesn't Clear After Save

### Problem
Form not reset after successful save.

### File
`/app/frontend/src/components/SaveDiagramModal.js` - handleSubmit function

### Buggy Code
```javascript
    setError('');
    onSave({ 
      title: title.trim(), 
      description: description.trim(),
      folder_id: folderId || null
    });
    // BUG: Form not reset after save
  };
```

### Fixed Code
```javascript
    setError('');
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
  };
```

---

## SAVE-006: Save Without Title Succeeds

### Problem
Pydantic model allows empty title.

### File
`/app/backend/server.py` - DiagramCreate model

### Buggy Code
```python
class DiagramCreate(BaseModel):
    title: str = Field(default="", max_length=200)  # BUG: No min_length validation
```

### Fixed Code
```python
class DiagramCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
```

---

## Quick Verification Commands

```bash
# Check current bug status
python manager.py status

# Inject all bugs (for new candidate)
python inject_bugs.py

# Inject by category
python inject_bugs.py --category "Authentication"
python inject_bugs.py --category "Save/Load"

# Fix all bugs (to verify solution)
python fix_bugs.py

# Evaluate candidate
python evaluate.py --candidate "Candidate Name" --html
```

---

## Score Interpretation

| Score | Grade | Assessment |
|-------|-------|-----------|
| 60-70 | A | Excellent - Fixed most/all bugs |
| 45-59 | B | Good - Fixed majority of bugs |
| 30-44 | C | Average - Fixed some bugs |
| 15-29 | D | Below Average - Missed many bugs |
| 0-14 | F | Needs Improvement |

---

## Common Candidate Mistakes

1. **AUTH-001**: Forgetting to also normalize email in signup
2. **AUTH-002**: Just uncommenting without adding `.lower()`
3. **AUTH-003**: Clearing token in wrong location
4. **AUTH-004**: Adding validation in frontend only (backend still vulnerable)
5. **SAVE-001**: Not understanding the upsert pattern
6. **SAVE-002**: Setting wrong state variable
7. **SAVE-003**: Adding setIsSaving(false) only in try block, not finally
8. **SAVE-004**: Not understanding data flow from API response
9. **SAVE-005**: Resetting form unconditionally (breaks edit mode)
10. **SAVE-006**: Adding frontend validation only (backend still accepts)
