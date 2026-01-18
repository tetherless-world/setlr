# Error Tracing Analysis

This document shows various challenging error scenarios and evaluates how well the current error messages help debug them.

## Test Scenarios

### Scenario 1: NoneType/NaN Attribute Access ✅ CLEAR
**Problem:** Calling `.strip()` on a missing/NaN value
**File:** `error_scenario1.setl.ttl`
**CSV Data:** Row 2 has empty Name field

**Error Output:**
```
Error rendering Jinja2 template: {{row.Name.strip().upper()}}
Transform: [...], Row: 1
Error type: UndefinedError
Error message: 'float object' has no attribute 'strip'
Row data: {'ID': '2', 'Name': nan, 'Age': '30'}
```

**Analysis:** ✅ Very clear! Shows:
- The problematic template
- Which row failed (row 1 = second data row)
- The actual row data showing `Name: nan`
- Clear error message

**Possible Improvement:** Could explicitly note "Name field is empty/missing" rather than just showing `nan`

---

### Scenario 2: Undefined Variable in Template ⚠️ SILENT FAILURE
**Problem:** Using `tags` instead of `tag` in the @for loop body
**File:** `error_scenario2.setl.ttl`

**Error Output:**
```
(No error - succeeds with empty value)
```

**Analysis:** ⚠️ This doesn't fail because Jinja2 by default treats undefined variables as empty strings. While this is standard Jinja2 behavior, it can be confusing. The typo `{{tags}}` instead of `{{tag}}` is silently ignored.

**Possible Improvement:** Consider using Jinja2's StrictUndefined mode to catch these errors, or add validation warnings.

---

### Scenario 3: Mismatched JSON Brackets ✅ CLEAR
**Problem:** Missing closing brace in nested JSON object
**File:** `error_scenario3.setl.ttl`

**Error Output:**
```
Error parsing JSON-LD template for transform [...]
JSON parsing error at line 9, column 1: Expecting ',' delimiter
Template context:
    6:       "email": "{{row.Email}}"
    7:     }
    8:   }
>>> 9: ]
```

**Analysis:** ✅ Clear! Shows exact location with context lines.

**Possible Improvement:** Show more context lines (maybe 6-8 lines before error) to help see the opening brace that wasn't closed.

---

### Scenario 4: Division by Zero in @if Conditional ✅ EXCELLENT
**Problem:** Dividing by zero when Count field is 0
**File:** `error_scenario4.setl.ttl`

**Error Output:**
```
Error evaluating @if conditional: int(row.Total) / int(row.Count) > 50
Transform: [...], Row: 1
Error type: ZeroDivisionError
Error message: division by zero
Row-specific variables:
  row: ID=2, Name=Bob, Total=150, Count=0
```

**Analysis:** ✅ Excellent! Clearly shows:
- The exact conditional expression
- The row data showing Count=0
- The error type

This is very easy to debug.

---

## Recommendations for Improvement

1. **NaN/Missing Value Clarity** (Minor)
   - When showing row data with NaN values, add a note: "Name: <empty/missing>"
   - This makes it immediately obvious without requiring knowledge of pandas internals

2. **JSON Context Lines** (Minor)
   - Increase context from 3-4 lines before error to 6-8 lines
   - This helps with mismatched bracket errors in deeply nested structures

3. **Undefined Variable Detection** (Optional - Breaking Change)
   - Consider adding a warning mode that logs when undefined variables are encountered
   - Or document the current behavior clearly
   - This would require Jinja2 StrictUndefined mode which might break existing templates

4. **Transform Name/Description** (Enhancement)
   - If the transform has a label or description in the SETL file, include it in error messages
   - Makes it easier to identify which transform failed in complex workflows

## Conclusion

The current error messages are **very effective** for most scenarios. The improvements suggested are minor enhancements rather than critical issues. The error context, row data, and specific error types make debugging significantly easier than before.

---

## Improvements Implemented

Based on the analysis, the following improvements have been made:

### 1. ✅ Better NaN/Missing Value Display
**Change:** When displaying row data in error messages, NaN values are now shown as `<empty/missing>` instead of `nan`.

**Before:**
```
Row data: {'ID': '2', 'Name': nan, 'Age': '30'}
```

**After:**
```
Row data: {'ID': '2', 'Name': '<empty/missing>', 'Age': '30'}
```

This makes it immediately obvious that the Name field is empty without requiring knowledge of pandas internals.

### 2. ✅ Increased JSON Context Lines
**Change:** Increased context lines from 4 before/3 after to 8 before/3 after for JSON parsing errors.

**Before:**
```
Template context:
    6:       "email": "{{row.Email}}"
    7:     }
    8:   }
>>> 9: ]
```

**After:**
```
Template context:
    2:   "@id": "https://example.com/test3/{{row.ID}}",
    3:   "profile": {
    4:     "name": "{{row.Name}}",
    5:     "contact": {
    6:       "email": "{{row.Email}}"
    7:     }
    8:   }
>>> 9: ]
```

Now you can see the opening brace on line 3, making it much easier to identify mismatched brackets.

---

## Testing Results

All error scenarios were tested after improvements:

✅ **Scenario 1 (NaN/Missing):** Error message now clearly shows `<empty/missing>` for the Name field
✅ **Scenario 3 (JSON Brackets):** Extended context now shows opening braces, making bracket matching easier
✅ **Scenario 4 (Division by Zero):** Already excellent, unchanged
✅ **All existing unit tests pass**

The error messages are now even more informative and user-friendly!
