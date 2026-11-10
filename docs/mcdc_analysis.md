# B3. Condition Coverage and MC/DC Analysis

**Course:** SE3002 Software Quality Engineering  
**Artifact:** Assignment 2 — Condition Coverage & MC/DC  
**Function Analyzed:** `registration_decision(student, course)` and `prerequisites_satisfied(completed, required)`

> [!NOTE]
> `pytest-cov` does not measure condition coverage or MC/DC. All analysis in this document is performed **manually** by inspection of the Python source code and Python's short-circuit evaluation semantics. Test cases map to `test_whitebox.py` and `test_blackbox.py` test IDs.

---

## 1. Identification of Atomic Conditions per Decision Point

Each `if` statement in `registration_decision` is analyzed for its atomic conditions.

### 1.1 Decision at Line 46

```python
if student.outstanding_dues < 0:
```
| Atomic Condition | Symbol | Description |
|:---|:---:|:---|
| `student.outstanding_dues < 0` | $A_1$ | Student has negative (invalid) dues |

This is a simple decision with **1 atomic condition** ($A_1$). No short-circuit complexity.

---

### 1.2 Decision at Line 48 (Compound with Short-Circuit)

```python
if not 0 <= course.enrolled <= course.capacity or course.capacity < 1:
```

Python evaluates this as:
$$(\lnot(0 \le e \le c)) \lor (c < 1)$$

Atomic conditions:
| Symbol | Condition | Evaluated When |
|:---:|:---|:---|
| $B_1$ | `course.enrolled < 0` | Always (first step of chained comparison) |
| $B_2$ | `course.enrolled > course.capacity` | Only when $B_1$ is False ($e \ge 0$) |
| $B_3$ | `course.capacity < 1` | Only when both $B_1$ and $B_2$ are False (enrolled in valid range) |

**Short-circuit behaviour:** If $B_1$ is True (enrolled < 0), neither $B_2$ nor $B_3$ is evaluated. If $B_1$ is False and $B_2$ is True (enrolled > capacity), $B_3$ is not evaluated.

---

### 1.3 Decision at Line 50

```python
if student.outstanding_dues > 1000:
```
| Symbol | Condition |
|:---:|:---|
| $C_1$ | `student.outstanding_dues > 1000` |

Simple decision, 1 atomic condition.

---

### 1.4 Decision at Line 52

```python
if course.code in student.registered_courses:
```
| Symbol | Condition |
|:---:|:---|
| $D_1$ | `course.code in student.registered_courses` |

Simple decision, 1 atomic condition.

---

### 1.5 Decision at Line 54

```python
if not prerequisites_satisfied(student.completed_courses, course.prerequisites):
```
Inside `prerequisites_satisfied`:
```python
if not required:
    return True
return bool(completed.intersection(required))
```

For the outer decision (at line 54 of `registration_decision`):
| Symbol | Condition |
|:---:|:---|
| $E_1$ | `prerequisites_satisfied(...)` returns `False` |

The function's compound logic:
| Symbol | Internal Condition |
|:---:|:---|
| $E_{1a}$ | `not required` (required set is empty) |
| $E_{1b}$ | `bool(completed.intersection(required))` |

---

### 1.6 Decision at Line 56 (Primary MC/DC Target)

```python
if not check_credit_limit(student.current_credits, course.credit_hours):
```
Inside `check_credit_limit`:
```python
if not 0 <= current_credits <= 18:
    raise ValueError("Invalid current credits")
if not 1 <= new_credits <= 4:
    raise ValueError("Invalid course credits")
return current_credits + new_credits < 18
```

The binary outcome of `check_credit_limit` for valid inputs:

| Symbol | Compound Condition | Composed From |
|:---:|:---|:---|
| $F_1$ | `current_credits + new_credits < 18` | The Boolean return value |

---

### 1.7 Decision at Line 58

```python
if course.enrolled > course.capacity:
```
| Symbol | Condition |
|:---:|:---|
| $G_1$ | `course.enrolled > course.capacity` |

---

## 2. Full Condition Coverage Truth Table for `registration_decision`

**Condition Coverage Definition:** Every atomic condition must be True in at least one test case and False in at least one test case.

| Test Case | $A_1$<br>`dues<0` | $B_1$<br>`enrolled<0` | $B_2$<br>`enrolled>cap` | $B_3$<br>`cap<1` | $C_1$<br>`dues>1000` | $D_1$<br>`in registered` | $E_1$<br>`prereq fails` | $F_1$<br>`credits >= 18` | $G_1$<br>`enrolled>cap` | Decision Outcome |
|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---|
| **TC-C1** | **T** | N/E | N/E | N/E | N/E | N/E | N/E | N/E | N/E | ValueError("Invalid dues") |
| **TC-C2** | F | **T** | N/E | N/E | N/E | N/E | N/E | N/E | N/E | ValueError("Invalid capacity...") |
| **TC-C3** | F | F | **T** | N/E | N/E | N/E | N/E | N/E | N/E | ValueError("Invalid capacity...") |
| **TC-C4** | F | F | F | **T** | N/E | N/E | N/E | N/E | N/E | ValueError("Invalid capacity...") |
| **TC-C5** | F | F | F | F | **T** | N/E | N/E | N/E | N/E | "DUES_BLOCK" |
| **TC-C6** | F | F | F | F | F | **T** | N/E | N/E | N/E | "ALREADY_REGISTERED" |
| **TC-C7** | F | F | F | F | F | F | **T** | N/E | N/E | "PREREQUISITES_MISSING" |
| **TC-C8** | F | F | F | F | F | F | F | **T** | N/E | "CREDIT_LIMIT" |
| **TC-C9** | F | F | F | F | F | F | F | F | **T** | "WAITLISTED" (structural path) |
| **TC-C10** | F | F | F | F | F | F | F | F | F | "REGISTERED" |

**Coverage Summary:**
| Condition Symbol | True in Test | False in Test | Fully Covered? |
|:---:|:---:|:---:|:---:|
| $A_1$ | TC-C1 | TC-C2 | ✅ |
| $B_1$ | TC-C2 | TC-C3 | ✅ |
| $B_2$ | TC-C3 | TC-C4 | ✅ |
| $B_3$ | TC-C4 | TC-C5 | ✅ |
| $C_1$ | TC-C5 | TC-C6 | ✅ |
| $D_1$ | TC-C6 | TC-C7 | ✅ |
| $E_1$ | TC-C7 | TC-C8 | ✅ |
| $F_1$ | TC-C8 | TC-C9/10 | ✅ |
| $G_1$ | TC-C9 | TC-C10 | ✅ |

> [!NOTE]
> N/E = Not Evaluated (Python short-circuit evaluation stops before reaching this condition). Condition coverage requires True and False, NOT "evaluated True and evaluated False". A condition that is N/E in all tests would not be covered. Here all conditions are reached via Python's sequential evaluation model.

---

## 3. MC/DC Analysis — Primary Focus: `prerequisites_satisfied` Compound Decision

The function `prerequisites_satisfied` contains a compound Boolean decision most suitable for MC/DC demonstration:

```python
def prerequisites_satisfied(completed: set[str], required: set[str]) -> bool:
    if not required:          # Condition P: required is empty
        return True
    return bool(completed.intersection(required))  # Condition Q: intersection is non-empty
```

For the case where `required` is non-empty (i.e., P is False), the return depends entirely on condition Q.

### 3.1 Atomic Conditions

| Symbol | Condition | Description |
|:---:|:---|:---|
| **P** | `not required` | The prerequisites set is empty |
| **Q** | `bool(completed.intersection(required))` | At least one required course is in completed courses |

> [!NOTE]
> `P` and `Q` are **not simultaneously evaluated**: when P is True, Q is not evaluated (short-circuit; the function returns `True` immediately). This means MC/DC must be demonstrated for each condition in its evaluation context.

### 3.2 Short-Circuit Truth Table

| Test | P (required empty?) | Q (intersection?) | Q Evaluated? | Outcome |
|:---:|:---:|:---:|:---:|:---:|
| **MC-P1** | **T** | N/E | No | True |
| **MC-P2** | **F** | **T** | Yes | True |
| **MC-P3** | **F** | **F** | Yes | False |

### 3.3 MC/DC Independent Effect Pairs

#### Condition P: `not required`

Pair: **MC-P1 vs MC-P2**

| Attribute | MC-P1 | MC-P2 |
|:---|:---:|:---:|
| **P** (required empty?) | **T** | **F** |
| **Q** (intersection?) | N/E | **T** (held True) |
| **Outcome** | True | True |

> [!WARNING]
> When P changes from T → F, the outcome does not change (True → True), because Q is True in MC-P2. For MC/DC, we need P's change to independently change the overall outcome. We need to hold Q constant at a value where P's change *matters*.

If Q is held False (MC-P3: outcome False) and P is changed to True, we get True (MC-P1). So:

**Pair for P (outcome-changing):** MC-P1 (P=T, Outcome=True) vs MC-P3 (P=F, Q=F, Outcome=False)

| Attribute | MC-P1 | MC-P3 |
|:---|:---:|:---:|
| **P** | **T** (required empty) | **F** (required non-empty) |
| **Q** | N/E | **F** (intersection empty) |
| **Outcome** | **True** | **False** |
| **P alone changes outcome?** | ✅ Yes — only P differs, outcome changes |

#### Condition Q: `bool(completed.intersection(required))`

Pair: **MC-P2 vs MC-P3**

| Attribute | MC-P2 | MC-P3 |
|:---|:---:|:---:|
| **P** | **F** (identical — held constant) | **F** (identical — held constant) |
| **Q** | **T** (non-empty intersection) | **F** (empty intersection) |
| **Outcome** | **True** | **False** |
| **Q alone changes outcome?** | ✅ Yes — only Q differs, outcome changes |

### 3.4 MC/DC Summary Table

| MC/DC Pair | Condition Demonstrated | P (MC-X) | Q (MC-X) | Outcome (MC-X) | P (MC-Y) | Q (MC-Y) | Outcome (MC-Y) | Independent? |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **MC-P1 vs MC-P3** | P independently changes outcome | T | N/E | True | F | F | False | ✅ Yes |
| **MC-P2 vs MC-P3** | Q independently changes outcome | F | T | True | F | F | False | ✅ Yes |

> [!IMPORTANT]
> **Implementation Defect Found:** The current implementation uses `bool(completed.intersection(required))`, which returns True if *any* prerequisite is completed (OR logic). The requirement FR-03 specifies **every** required course must be in `completed` (AND logic). The correct implementation should be `required.issubset(completed)`. This defect is exposed by the failing black-box test `test_prerequisite_equivalence_classes[completed3-required3-False]` where `completed={CS101}`, `required={CS101, MATH101}` should return False but returns True.

---

## 4. Corresponding Test Pairs from Test Files

| MC/DC Test Case | Corresponding pytest Test ID | File |
|:---|:---|:---:|
| MC-P1 (P=T, empty required) | `test_prerequisite_equivalence_classes[completed0-required0-True]` | `test_blackbox.py` |
| MC-P2 (P=F, Q=T) | `test_prerequisite_equivalence_classes[completed1-required1-True]` | `test_blackbox.py` |
| MC-P3 (P=F, Q=F) | `test_prerequisite_equivalence_classes[completed4-required4-False]` | `test_blackbox.py` |
| Structural MC path (G1=T) | `test_wb_struct_waitlist_decision_line59` | `test_whitebox.py` |
| Structural MC path (G1=F) | `test_wb_decision_return_paths[s5-c5-REGISTERED]` | `test_whitebox.py` |

---

## 5. MC/DC for Line 48 Compound Expression (Advanced)

The compound expression:
```python
not 0 <= course.enrolled <= course.capacity or course.capacity < 1
```

Atomic conditions: $B_1 = (e < 0)$, $B_2 = (e > c)$, $B_3 = (c < 1)$  
Overall decision $D = B_1 \lor B_2 \lor B_3$

For MC/DC on a 3-condition OR:

| MC/DC Pair | Changed Condition | $B_1$ | $B_2$ | $B_3$ | $D$ |
|:---:|:---:|:---:|:---:|:---:|:---:|
| TC-C2 | — (baseline $B_1$=T) | T | N/E | N/E | T |
| TC-C3 (held $B_1$=F, changed $B_2$) | — | F | T | N/E | T |
| TC-C4 (held $B_1$=F, $B_2$=F, changed $B_3$) | — | F | F | T | T |
| TC-C5 (all False) | — | F | F | F | F |

**MC/DC Pairs for 3-way OR:**
- $B_1$: TC-C2 ($B_1$=T, D=T) vs TC-C3/4/5 (must hold $B_2$=F, $B_3$=F, change $B_1$: TC-C2 T→F gives TC-C5) ✅
- $B_2$: TC-C3 ($B_2$=T, D=T) vs TC-C5 (all F, D=F) ✅ 
- $B_3$: TC-C4 ($B_3$=T, D=T) vs TC-C5 (all F, D=F) ✅

---

## 6. Python Short-Circuit Account (Formal)

Python evaluates expressions **strictly left-to-right, stopping as soon as the result is determined**. The significance for condition/MC/DC analysis:

| Short-Circuit Rule | Python Operator | Effect on Coverage |
|:---|:---:|:---|
| `A and B`: if A=False, B not evaluated | `and` | B receives N/E (Not Evaluated) when A is False |
| `A or B`: if A=True, B not evaluated | `or` | B receives N/E (Not Evaluated) when A is True |
| `a <= b <= c` = `a <= b and b <= c` | Chained comparison | Second comparison N/E if first is False |
| `not (...)` | `not` | Wraps the sub-expression; short-circuit is within sub-expression |

For condition coverage, N/E is treated distinctly from "evaluated False." An atomic condition does not get credit for a False outcome if it was never evaluated. Our test set is designed such that every atomic condition has at least one test where it is explicitly evaluated to True and at least one where it is evaluated to False (not merely skipped).
