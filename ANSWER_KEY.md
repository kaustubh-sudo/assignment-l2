# Answer Key - Bug Fixes (CONFIDENTIAL)

> ⚠️ **FOR ASSESSORS ONLY** - Do not share with candidates

---

## AUTH-001: Email Case-Sensitive Login

### Problem
The login endpoint performs a case-sensitive email lookup, so `Test@Example.com` and `test@example.com` are treated as different users.

### File
`/app/backend/server.py`

### Location
Login endpoint (`/api/auth/login`) - Line ~194

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

### Explanation
Adding `.lower()` normalizes the email to lowercase before querying the database. This ensures case-insensitive matching.

**Note:** For a complete solution, the signup endpoint should also normalize emails to lowercase when storing them.

---

## AUTH-002: Duplicate Email Registration Allowed

### Problem
The duplicate email check is commented out, allowing users to register with the same email multiple times.

### File
`/app/backend/server.py`

### Location
Signup endpoint (`/api/auth/signup`) - Line ~161-167

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

### Explanation
1. Uncomment the duplicate check logic
2. Use `.lower()` for case-insensitive duplicate detection

---

## AUTH-003: Logout Doesn't Clear Token

### Problem
The logout function sets state to null but doesn't remove the token from localStorage, allowing users to remain authenticated after "logging out".

### File
`/app/frontend/src/context/AuthContext.js`

### Location
`logout` function - Line ~113-117

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

### Explanation
The `localStorage.removeItem('token')` line must be present to actually clear the persisted token. Without it, the token remains in localStorage and the user can still access protected routes by refreshing the page.

---

## Quick Verification Commands

```bash
# Check current bug status
python manager.py status

# Inject all bugs (for new candidate)
python inject_bugs.py

# Fix all bugs (to verify solution)
python fix_bugs.py

# Evaluate candidate
python evaluate.py --candidate "Candidate Name" --html
```

---

## Scoring Guide

| Bug ID | Difficulty | Points |
|--------|-----------|--------|
| AUTH-001 | Easy | 1 |
| AUTH-002 | Easy | 1 |
| AUTH-003 | Easy | 1 |
| **Total** | | **3** |

### Score Interpretation
- **3/3 (100%)**: Excellent - Found and fixed all bugs
- **2/3 (67%)**: Good - Missed one bug
- **1/3 (33%)**: Needs improvement
- **0/3 (0%)**: Did not complete assessment

---

## Common Candidate Mistakes

1. **AUTH-001**: Forgetting to also normalize email in signup (partial fix)
2. **AUTH-002**: Just uncommenting without adding `.lower()`
3. **AUTH-003**: Clearing token in wrong location or using wrong method

---

## Notes for Assessors

- The evaluation script automatically detects if bugs are fixed by checking for the presence of specific code patterns
- Candidates may fix bugs in different ways that achieve the same result - manual review may be needed
- Time taken is not tracked by the script - assessors should note this separately
