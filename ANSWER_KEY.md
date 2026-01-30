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
| EXPORT-001 | Export | Easy | 5 | DiagramRenderer.js |
| EXPORT-002 | Export | Medium | 10 | DiagramRenderer.js |
| EXPORT-003 | Export | Easy | 5 | PreviewPanel.js |
| SEARCH-001 | Search | Easy | 5 | DiagramsList.js |
| SEARCH-002 | Search | Medium | 10 | DiagramsList.js |
| SEARCH-003 | Search | Medium | 10 | DiagramsList.js |
| SEARCH-004 | Search | Easy | 5 | DiagramsList.js |
| **Total** | | | **170** | |

---

## Authentication Bugs

### AUTH-001: Email Case-Sensitive Login
**File:** `/app/backend/server.py`
```python
# Buggy
user_doc = await db.users.find_one({"email": credentials.email})

# Fixed
user_doc = await db.users.find_one({"email": credentials.email.lower()})
```

### AUTH-002: Duplicate Email Registration
**File:** `/app/backend/server.py`
```python
# Buggy: check is commented out
# Fixed: uncomment and add .lower()
existing_user = await db.users.find_one({"email": user_data.email.lower()})
if existing_user:
    raise HTTPException(status_code=400, detail="Email already registered")
```

### AUTH-003: Logout Doesn't Clear Token
**File:** `/app/frontend/src/context/AuthContext.js`
```javascript
// Buggy
const logout = () => {
  // Token removal disabled
  setToken(null);
  setUser(null);
};

// Fixed
const logout = () => {
  localStorage.removeItem('token');
  setToken(null);
  setUser(null);
};
```

### AUTH-004: Password Minimum Length
**File:** `/app/backend/server.py`
```python
# Add before user creation
if len(user_data.password) < 6:
    raise HTTPException(status_code=400, detail="Password must be at least 6 characters")
```

---

## Save/Load Bugs

### SAVE-001: Duplicate Entries
**File:** `/app/backend/server.py`
```python
# Add duplicate check before insert
existing_diagram = await db.diagrams.find_one({
    "user_id": current_user.user_id,
    "title": diagram_data.title
})
if existing_diagram:
    # Update existing instead
```

### SAVE-002: Load Doesn't Populate Description
**File:** `/app/frontend/src/pages/DiagramRenderer.js`
```javascript
// Add this line when loading
setUserInput(data.description || '');
```

### SAVE-003: Save Button Stays Disabled
**File:** `/app/frontend/src/pages/DiagramRenderer.js`
```javascript
// Add finally block
} finally {
  setIsSaving(false);
}
```

### SAVE-004: Timestamp Doesn't Update
**File:** `/app/frontend/src/pages/DiagramRenderer.js`
```javascript
// Use data.updated_at instead of savedDiagram?.updated_at
updated_at: data.updated_at
```

### SAVE-005: Title Doesn't Clear
**File:** `/app/frontend/src/components/SaveDiagramModal.js`
```javascript
// Add form reset after save
if (!existingTitle) {
  setTitle('');
  setDescription('');
}
```

### SAVE-006: Empty Title Accepted
**File:** `/app/backend/server.py`
```python
# Use min_length=1 in Pydantic model
title: str = Field(..., min_length=1, max_length=200)
```

---

## List/Display Bugs

### LIST-001: Shows Everyone's Diagrams
**File:** `/app/backend/server.py`
```python
# Add user filter
query_filter = {"user_id": current_user.user_id}
```

### LIST-002: Delete Wrong Diagram
**File:** `/app/frontend/src/components/DiagramCard.js`
```javascript
// Fix: pass correct diagram
onDelete(diagram);  // Not diagram with corrupted ID
```

### LIST-003: Sorted Oldest First
**File:** `/app/backend/server.py`
```python
sort_direction = -1  # Not 1
```

### LIST-004: Count Doesn't Update
**File:** `/app/frontend/src/pages/DiagramsList.js`
```javascript
// Add state update
setDiagrams(prevDiagrams => prevDiagrams.filter(d => d.id !== deleteTarget.id));
```

### LIST-005: Raw Date Format
**File:** `/app/frontend/src/components/DiagramCard.js`
```javascript
// Use formatDate function
{formatDate(diagram.created_at)}
```

---

## Export Bugs

### EXPORT-001: Generic Filename
**File:** `/app/frontend/src/pages/DiagramRenderer.js`
```javascript
// Use title in filename
const sanitizedTitle = title.toLowerCase().replace(/[^a-z0-9]+/g, '-');
return `${sanitizedTitle}.${format}`;
```

### EXPORT-002: Spinner Never Clears
**File:** `/app/frontend/src/pages/DiagramRenderer.js`
```javascript
// Add finally block
} finally {
  setIsExporting(false);
}
```

### EXPORT-003: Button Not Disabled
**File:** `/app/frontend/src/components/PreviewPanel.js`
```javascript
// Add disabled prop
<Button disabled={isExporting} ...>
```

---

## Search Bugs

### SEARCH-001: Case-Sensitive Search
**File:** `/app/frontend/src/pages/DiagramsList.js`
```javascript
// Add toLowerCase()
const query = debouncedSearchQuery.toLowerCase().trim();
diagram.title.toLowerCase().includes(query)
```

### SEARCH-002: Ignores Folder Filter
**File:** `/app/frontend/src/pages/DiagramsList.js`
```javascript
// Apply folder filter BEFORE search filter (always)
// Not only when not searching
```

### SEARCH-003: Clear Button Doesn't Work
**File:** `/app/frontend/src/pages/DiagramsList.js`
```javascript
// Add setSearchQuery('')
const handleClearSearch = () => {
  setSearchQuery('');
};
```

### SEARCH-004: No Debounce
**File:** `/app/frontend/src/pages/DiagramsList.js`
```javascript
// Use debounced value
const debouncedSearchQuery = useDebounce(searchQuery, 300);
```

---

## Quick Commands

```bash
# Check status
python manager.py status

# Inject all bugs
python inject_bugs.py

# Inject by category
python inject_bugs.py --category "Search"

# Fix all bugs
python fix_bugs.py

# Evaluate
python evaluate.py --candidate "Name" --html
```

---

## Score Interpretation

| Score | Grade | Assessment |
|-------|-------|-----------|
| 140-170 | A | Excellent |
| 110-139 | B | Good |
| 75-109 | C | Average |
| 40-74 | D | Below Average |
| 0-39 | F | Needs Improvement |
