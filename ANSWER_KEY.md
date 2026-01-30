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
| LIST-001 | List/Display | Hard | 15 | server.py |
| LIST-002 | List/Display | Medium | 10 | DiagramCard.js |
| LIST-003 | List/Display | Easy | 5 | server.py |
| LIST-004 | List/Display | Medium | 10 | DiagramsList.js |
| LIST-005 | List/Display | Easy | 5 | DiagramCard.js |
| **Total** | | | **120** | |

---

## AUTH-001: Email Case-Sensitive Login

### File: `/app/backend/server.py`

### Buggy Code
```python
user_doc = await db.users.find_one({"email": credentials.email})
```

### Fixed Code
```python
user_doc = await db.users.find_one({"email": credentials.email.lower()})
```

---

## AUTH-002: Duplicate Email Registration

### File: `/app/backend/server.py`

### Buggy Code
```python
# Check if user already exists - DISABLED FOR TESTING
# existing_user = await db.users.find_one(...)
```

### Fixed Code
```python
existing_user = await db.users.find_one({"email": user_data.email.lower()})
if existing_user:
    raise HTTPException(status_code=400, detail="Email already registered")
```

---

## AUTH-003: Logout Doesn't Clear Token

### File: `/app/frontend/src/context/AuthContext.js`

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

## AUTH-004: Password Minimum Length

### File: `/app/backend/server.py`

### Buggy Code
```python
# Password validation disabled for testing
```

### Fixed Code
```python
if len(user_data.password) < 6:
    raise HTTPException(status_code=400, detail="Password must be at least 6 characters")
```

---

## SAVE-001: Duplicate Entries

### File: `/app/backend/server.py`

### Buggy Code
```python
# Duplicate check disabled - allows multiple diagrams with same title
```

### Fixed Code
```python
existing_diagram = await db.diagrams.find_one({
    "user_id": current_user.user_id,
    "title": diagram_data.title
})
if existing_diagram:
    # Update existing instead of creating new
    await db.diagrams.update_one({"id": existing_diagram["id"]}, {"$set": update_data})
    return existing_diagram_response
```

---

## SAVE-002: Load Doesn't Populate Description

### File: `/app/frontend/src/pages/DiagramRenderer.js`

### Buggy Code
```javascript
// BUG: Not setting userInput from description
setSavedDiagram({...});
```

### Fixed Code
```javascript
setUserInput(data.description || '');
setSavedDiagram({...});
```

---

## SAVE-003: Save Button Stays Disabled

### File: `/app/frontend/src/pages/DiagramRenderer.js`

### Buggy Code
```javascript
} catch (err) {
  toast.error(err.message);
}
// BUG: Missing finally block
```

### Fixed Code
```javascript
} catch (err) {
  toast.error(err.message);
} finally {
  setIsSaving(false);
}
```

---

## SAVE-004: Timestamp Doesn't Update

### File: `/app/frontend/src/pages/DiagramRenderer.js`

### Buggy Code
```javascript
updated_at: savedDiagram?.updated_at  // BUG: Using old timestamp
```

### Fixed Code
```javascript
updated_at: data.updated_at
```

---

## SAVE-005: Title Doesn't Clear

### File: `/app/frontend/src/components/SaveDiagramModal.js`

### Buggy Code
```javascript
onSave({...});
// BUG: Form not reset after save
```

### Fixed Code
```javascript
onSave({...});
if (!existingTitle) {
  setTitle('');
  setDescription('');
}
```

---

## SAVE-006: Empty Title Accepted

### File: `/app/backend/server.py`

### Buggy Code
```python
title: str = Field(default="", max_length=200)  # BUG: No min_length
```

### Fixed Code
```python
title: str = Field(..., min_length=1, max_length=200)
```

---

## LIST-001: Shows Everyone's Diagrams

### File: `/app/backend/server.py`

### Buggy Code
```python
# BUG: Missing user_id filter - shows all diagrams
query_filter = {}
```

### Fixed Code
```python
query_filter = {"user_id": current_user.user_id}
```

---

## LIST-002: Delete Wrong Diagram

### File: `/app/frontend/src/components/DiagramCard.js`

### Buggy Code
```javascript
onDelete({ ...diagram, id: diagram.id + '_wrong' });  // BUG: Corrupted ID
```

### Fixed Code
```javascript
onDelete(diagram);
```

---

## LIST-003: Sorted Oldest First

### File: `/app/backend/server.py`

### Buggy Code
```python
sort_direction = 1  # BUG: ascending shows oldest first
```

### Fixed Code
```python
sort_direction = -1  # descending shows newest first
```

---

## LIST-004: Count Doesn't Update

### File: `/app/frontend/src/pages/DiagramsList.js`

### Buggy Code
```javascript
// Remove from local state - BUG: Not updating state correctly
toast.success('Diagram deleted successfully');
```

### Fixed Code
```javascript
setDiagrams(prevDiagrams => prevDiagrams.filter(d => d.id !== deleteTarget.id));
toast.success('Diagram deleted successfully');
```

---

## LIST-005: Raw Date Format

### File: `/app/frontend/src/components/DiagramCard.js`

### Buggy Code
```javascript
{diagram.created_at}
```

### Fixed Code
```javascript
{formatDate(diagram.created_at)}
```

---

## Quick Commands

```bash
# Check status
python manager.py status

# Inject all bugs
python inject_bugs.py

# Inject by category
python inject_bugs.py --category "Authentication"
python inject_bugs.py --category "Save/Load"
python inject_bugs.py --category "List/Display"

# Fix all bugs
python fix_bugs.py

# Evaluate
python evaluate.py --candidate "Name" --html
```

---

## Score Interpretation

| Score | Grade | Assessment |
|-------|-------|-----------|
| 100-120 | A | Excellent |
| 75-99 | B | Good |
| 50-74 | C | Average |
| 25-49 | D | Below Average |
| 0-24 | F | Needs Improvement |
