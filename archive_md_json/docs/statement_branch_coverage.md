# B2. Statement and Branch Coverage Analysis

**Course:** SE3002 Software Quality Engineering  
**Artifact:** Assignment 2 — Statement & Branch Coverage Report  
**Tool:** `pytest-cov` with `--cov-branch` flag  
**Subject File:** `registration.py` (53 statements, 26 branches)

---

## 1. Initial Coverage — Black-Box Tests Only (`test_blackbox.py`)

Command:
```bash
python -m pytest tests/test_blackbox.py --cov=registration --cov-branch --cov-report=term-missing
```

### 1.1 Raw Results

```
Name              Stmts   Miss Branch BrPart  Cover   Missing
-------------------------------------------------------------
registration.py      53      3     26      3    92%   51, 59, 71
```

| Metric | Executed | Total | Coverage % |
|:---|:---:|:---:|:---:|
| Statements | 50 | 53 | 94.3 % |
| Branches | 23 | 26 | 88.5 % |
| **Combined (pytest-cov)** | — | — | **92 %** |

### 1.2 Uncovered Locations (Initial State)

| Location | Line | Branch | Description | Why Not Covered |
|:---|:---:|:---:|:---|:---|
| `registration_decision` | **51** | `50 → 51` | `return "DUES_BLOCK"` | Implementation uses `> 1000` threshold; black-box tests use `dues=1` which is requirement-correct but never triggers `dues > 1000`. |
| `registration_decision` | **59** | `58 → 59` | `return "WAITLISTED"` | Line 48 traps `enrolled > capacity` with `ValueError` before line 58 is reached; structurally dead with static `Course` objects. |
| `register_course` | **71** | `70 → 71` | `course.waitlist.append(student.student_id)` | Downstream of line 59; unreachable until line 59 is reachable. |

---

## 2. Gap Analysis

| Gap ID | Location | Missing | Root Cause |
|:---|:---:|:---|:---|
| **GAP-1** | Line 50–51 | Branch `50→51` True | Implementation defect: `outstanding_dues > 1000` instead of `> 0`. Must drive `dues ≥ 1001` to trigger it. |
| **GAP-2** | Line 58–59 | Branch `58→59` True | Structural dead code: line 48 blocks `enrolled > capacity` before line 58; needs a `DynamicEnrollmentCourse` with different values on 1st vs 2nd `.enrolled` read. |
| **GAP-3** | Line 70–71 | Branch `70→71` True | Downstream of GAP-2; `register_course` can only reach line 71 after `registration_decision` returns `"WAITLISTED"`, which requires GAP-2 to be exercised. |

---

## 3. Structural White-Box Tests Added to `test_whitebox.py`

| Test ID | Closes Gap | Mechanism | Covered Line / Branch |
|:---|:---:|:---|:---|
| `test_wb13_dues_above_1000_causes_dues_block` | GAP-1 | `outstanding_dues=1001` → `dues > 1000` True | Line 51; Branch `50→51` |
| `test_wb14_waitlisted_branch_line59` | GAP-2 | `_DynamicEnrollmentCourse(first=5, second=11)` — read 1 at line 48 returns 5 (valid), read 2 at line 58 returns 11 (> capacity) | Line 59; Branch `58→59` |
| `test_wb15_register_course_waitlist_appends_new_student` | GAP-3 | `register_course` with dynamic course + student not in waitlist → appends | Line 71; Branch `70→71` |
| `test_wb16_register_course_no_duplicate_on_waitlist` | GAP-3 (False branch) | Student already in `waitlist` → branch condition at line 70 is False, skips append | Branch `70→72` |

---

## 4. Final Coverage — All Tests (`test_blackbox.py` + `test_whitebox.py`)

Command:
```bash
python -m pytest tests/test_blackbox.py tests/test_whitebox.py --cov=registration --cov-branch --cov-report=term-missing
```

### 4.1 Actual Results (Verified)

```
Name              Stmts   Miss Branch BrPart  Cover   Missing
-------------------------------------------------------------
registration.py      53      0     26      0   100%
-------------------------------------------------------------
TOTAL                53      0     26      0   100%
```

| Metric | Before (BB only) | After (BB + WB) |
|:---|:---:|:---:|
| Statements Covered | 50 / 53 (94.3 %) | **53 / 53 (100 %)** |
| Branches Covered | 23 / 26 (88.5 %) | **26 / 26 (100 %)** |
| Overall pytest-cov | 92 % | **100 %** |
| Missing Lines | 51, 59, 71 | *(none)* |
| Missing Branches | [50→51], [58→59], [70→71] | *(none)* |

> [!NOTE]
> Tests that **fail** (revealing implementation defects) still drive code execution. pytest-cov marks a line/branch covered when bytecode executes, regardless of assertion outcome. All four structural gap-closing tests **PASS**.

> [!IMPORTANT]
> The 15 failing tests (12 black-box + 3 white-box) are **deliberately kept** with requirement-correct expected values per the assignment guidelines: *"Record failing tests faithfully. Do not alter expected results to force tests to pass."* The failures document real implementation defects.

---

## 5. Uncovered Location Summary

| Line | Initial | Final | Fixed By |
|:---|:---:|:---:|:---|
| 51 (`return "DUES_BLOCK"`) | ❌ | ✅ | `test_wb13_dues_above_1000_causes_dues_block` |
| 59 (`return "WAITLISTED"`) | ❌ | ✅ | `test_wb14_waitlisted_branch_line59` |
| 71 (`waitlist.append(...)`) | ❌ | ✅ | `test_wb15_register_course_waitlist_appends_new_student` |
