# Candidate Brief: UserAuth Profile Data Sanitizer
**Assessment ID:** `BH-L1-002`  
**[CANDIDATE MATERIAL]**

---

## Welcome to the Team

Welcome to the backend engineering team at **UserAuth**. We maintain the identity onboarding services that clean and normalize profile payloads before writing user records to our database.

Recently, our customer support and database operations teams reported data integrity defects in our registration pipeline:
- Usernames with whitespace entered by mistake are creating duplicate lookup failures.
- Email addresses saved with uppercase characters are breaking case-sensitive unique index queries.
- User full names are displayed unformatted without proper capitalization.

You are assigned to investigate, reproduce, and fix the defects in our sanitization module.

---

## Running the Tests & Reproducing Defects (CLI)

Run the test suite directly:
```bash
python3 -m unittest discover tests
```
Observe how `test_bug_reproduction_whitespace_not_stripped` and `test_bug_reproduction_casing_not_normalized` fail:
```
AssertionError: '  johndoe  ' != 'johndoe'
```

---

## Your Objectives

1. **Investigate the Codebase:**
   - Inspect `src/profile_sanitizer.py` and its corresponding test suite `tests/test_profile_sanitizer.py`.
2. **Diagnose Root Cause:**
   - Understand why string method calls like `username.strip()` and `email.lower()` do not alter the returned profile dictionary.
3. **Implement the Fix:**
   - Modify `src/profile_sanitizer.py` to ensure all fields are cleaned, properly capitalized/lowercased, and trimmed.
   - Maintain the dictionary contract with `"username"`, `"email"`, `"full_name"`, and `"is_valid"`.
4. **Expand Test Coverage:**
   - Add tests covering edge cases: empty strings, mixed casing in email domains, multi-word names, whitespace tabs and newlines, and non-dict inputs.
5. **Prepare for Mentor Review:**
   - Be prepared to discuss Python string immutability, your fix, and edge case coverage during your technical interview.

---

## Rules and Guidelines

- Do not alter function signatures or expected output dictionary schema.
- Explain your technical findings and testing discipline clearly.
