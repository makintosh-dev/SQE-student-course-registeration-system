"""White-box tests for registration.py — SQE Assignment 2, Part B.

Each test is tagged with:
  Target   : the specific branch, condition, basis path, or MC/DC pair exercised.
  Covers   : the registration.py line(s) / branch(es) driven by the test.
  Expected : the value the *code as written* returns (may differ from requirement
             when a known defect is present — marked with [DEFECT]).

Structural tests (WB-13 through WB-16) fill the three coverage gaps identified
in the initial black-box-only run (lines 51, 59, 71 uncovered).
"""

import pytest
from registration import (
    Student, Course,
    registration_decision, register_course,
    check_credit_limit, prerequisites_satisfied,
)


# ---------------------------------------------------------------------------
# Shared helper factories
# ---------------------------------------------------------------------------

def student(**kw):
    """Return a Student with safe defaults; override fields with **kw."""
    data = dict(
        student_id="W001",
        completed_courses={"P1", "P2"},
        current_credits=10,
        outstanding_dues=0,
        registered_courses=set(),
    )
    data.update(kw)
    return Student(**data)


def course(**kw):
    """Return a Course with safe defaults; override fields with **kw."""
    data = dict(
        code="C1",
        credit_hours=3,
        capacity=10,
        enrolled=5,
        prerequisites={"P1", "P2"},
        waitlist=[],
    )
    data.update(kw)
    return Course(**data)


class _DynamicEnrollmentCourse(Course):
    """Test-only Course subclass whose .enrolled property returns two
    different values on successive reads.

    Read 1 (at line 48, the guard): returns *first_enrolled*  → passes guard.
    Read 2 (at line 58, the waitlist check): returns *second_enrolled*.

    This lets the test drive the structurally-unreachable WAITLISTED branch
    (line 59) which cannot be reached via a normal immutable Course because
    any enrolled>capacity value is trapped at the validation guard on line 48.
    """

    def __init__(self, first_enrolled: int, second_enrolled: int, **kw):
        super().__init__(**kw)
        self._reads = iter([first_enrolled, second_enrolled])
        # Freeze the dataclass's own 'enrolled' field to a safe sentinel
        # so the dataclass setter doesn't interfere.
        object.__setattr__(self, "enrolled", first_enrolled)

    # Override property to intercept both reads
    @property  # type: ignore[override]
    def enrolled(self):  # type: ignore[override]
        try:
            return next(self._reads)
        except StopIteration:
            # Safety fallback for any extra reads
            return 0

    @enrolled.setter
    def enrolled(self, value):
        # Let the dataclass __init__ call pass silently
        pass


# ---------------------------------------------------------------------------
# WB-01 / WB-02 — Exception guard edges (basis paths 1–4)
# ---------------------------------------------------------------------------

def test_wb01_negative_dues_raises_value_error():
    """
    Target  : Branch line 46 → True → raise ValueError("Invalid dues")
    Path    : Basis Path 1  (Node 1 → 2 → 3 → X)
    Covers  : Line 47 (raise); Branch 46→47
    """
    with pytest.raises(ValueError, match="Invalid dues"):
        registration_decision(student(outstanding_dues=-1), course())


def test_wb02_enrolled_below_zero_raises():
    """
    Target  : Branch 4a → True (enrolled < 0) → raise ValueError
    Path    : Basis Path 2  (short-circuit: B1 is True)
    Covers  : Line 49 (raise); Branch 48 short-circuit path B1=T
    """
    with pytest.raises(ValueError, match="Invalid capacity or enrollment"):
        registration_decision(student(), course(enrolled=-1, capacity=10))


def test_wb02b_enrolled_above_capacity_raises():
    """
    Target  : Branch 4b → True (enrolled > capacity) → raise ValueError
    Path    : Basis Path 3  (short-circuit: B1=F, B2=T)
    Covers  : Line 49 (raise); Branch 48 short-circuit path B2=T
    """
    with pytest.raises(ValueError, match="Invalid capacity or enrollment"):
        registration_decision(student(), course(enrolled=11, capacity=10))


def test_wb02c_capacity_below_one_raises():
    """
    Target  : Branch 4c → True (capacity < 1) → raise ValueError
    Path    : Basis Path 4  (short-circuit: B1=F, B2=F, B3=T)
    Covers  : Line 49 (raise); Branch 48 short-circuit path B3=T
    """
    with pytest.raises(ValueError, match="Invalid capacity or enrollment"):
        registration_decision(student(), course(enrolled=0, capacity=0))


# ---------------------------------------------------------------------------
# WB-03 through WB-08 — All six ordered decision return paths (paths 5–10)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("s,c,expected", [
    # WB-03  Basis Path 5 — dues > 1000 True branch (DEFECT: threshold bug)
    (student(outstanding_dues=1),    course(),              "DUES_BLOCK"),
    # WB-04  Basis Path 6 — already-registered True branch
    (student(registered_courses={"C1"}), course(),         "ALREADY_REGISTERED"),
    # WB-05  Basis Path 7 — prerequisites unsatisfied True branch
    (student(completed_courses=set()), course(),           "PREREQUISITES_MISSING"),
    # WB-06  Basis Path 8 — credit limit exceeded True branch
    (student(current_credits=16),    course(),              "CREDIT_LIMIT"),
    # WB-07  Basis Path 9 — enrolled > capacity at line 58 (uses dynamic course)
    # (covered by WB-13 below; listed here for parametrize completeness but
    #  note enrolled=10 == capacity so code returns REGISTERED due to bug at 58)
    (student(),                      course(enrolled=10),   "WAITLISTED"),
    # WB-08  Basis Path 10 — normal REGISTERED return
    (student(),                      course(enrolled=9),    "REGISTERED"),
])
def test_wb_decision_return_paths(s, c, expected):
    """
    Target  : Each if-branch in registration_decision exercised in isolation.
    Covers  : Lines 51, 53, 55, 57, 59, 60; all True/False branches of
              lines 50, 52, 54, 56, 58.
    Note    : WB-03 and WB-07 FAIL because of implementation defects
              (dues threshold is > 1000 not > 0; waitlist uses > not >=).
              The expected values here are REQUIREMENTS.md-correct.
    """
    assert registration_decision(s, c) == expected


# ---------------------------------------------------------------------------
# WB-09 through WB-12 — Atomic-condition False-side isolation (condition cov.)
# ---------------------------------------------------------------------------

def test_wb09_dues_zero_not_blocked():
    """
    Target  : Condition C1 (dues > 1000) → False side; ensure dues=0 passes.
    Covers  : Branch 50→False path (falls through to line 52).
    MC/DC   : C1=F half of the C1 independent-effect pair.
    """
    assert registration_decision(student(outstanding_dues=0), course()) == "REGISTERED"


def test_wb10_not_already_registered():
    """
    Target  : Condition D1 (code in registered_courses) → False side.
    Covers  : Branch 52→False path.
    MC/DC   : D1=F half of the D1 independent-effect pair.
    """
    assert registration_decision(student(registered_courses=set()), course()) == "REGISTERED"


def test_wb11_prerequisites_fully_met():
    """
    Target  : Condition E1 (prereqs_satisfied returns False) → False side.
    Covers  : Branch 54→False path (all prereqs met).
    MC/DC   : E1=F half of the E1 independent-effect pair (prereqs complete).
    """
    assert registration_decision(
        student(completed_courses={"P1", "P2"}), course()
    ) == "REGISTERED"


def test_wb12_credit_boundary_exactly_eighteen():
    """
    Target  : Condition F1 (current + new >= 18) boundary.  15+3=18 is at the
              defective '<18' boundary — the code returns CREDIT_LIMIT (bug).
    Covers  : Branch 56→True (credit limit exceeded according to buggy impl).
    Note    : [DEFECT] FR-01 says <=18 is allowed; implementation uses <18.
              This test therefore FAILS and documents the defect faithfully.
    """
    # Code uses <18 so 15+3=18 is rejected (CREDIT_LIMIT), not REGISTERED.
    assert registration_decision(
        student(current_credits=15), course(credit_hours=3)
    ) == "REGISTERED"  # requirement-correct; will FAIL against buggy impl


def test_wb12b_credit_well_within_limit():
    """
    Target  : Branch 56→False side (credit limit NOT exceeded).
    Covers  : Fall-through from line 56 to line 58.
    """
    assert registration_decision(
        student(current_credits=10), course(credit_hours=3)
    ) == "REGISTERED"


def test_wb12c_credit_one_below_limit():
    """
    Target  : Condition F1 False side — 14+3=17 < 18, check_credit_limit=True,
              so not True = False → does NOT return CREDIT_LIMIT.
    Covers  : Branch 56→False path.
    """
    assert registration_decision(
        student(current_credits=14), course(credit_hours=3)
    ) == "REGISTERED"


def test_wb12d_seat_available_below_capacity():
    """
    Target  : Condition G1 (enrolled > capacity) → False side.
    Covers  : Branch 58→False → line 60 "REGISTERED".
    MC/DC   : G1=F half of the G1 independent-effect pair.
    """
    assert registration_decision(
        student(), course(enrolled=9, capacity=10)
    ) == "REGISTERED"


# ---------------------------------------------------------------------------
# WB-13 — STRUCTURAL: cover Line 51 / Branch 50→51 (GAP-1)
# ---------------------------------------------------------------------------

def test_wb13_dues_above_1000_causes_dues_block():
    """
    Target  : Condition C1 (outstanding_dues > 1000) → True side.
    Path    : Basis Path 5 fully exercised.
    Covers  : Line 51 'return "DUES_BLOCK"'; Branch 50→51.
    Gap     : Line 51 was NOT covered by any black-box test because the
              implementation uses >1000 whereas tests used dues=1 (which
              satisfies the requirement but doesn't trigger the buggy threshold).
    Note    : This test PASSES against the implementation (dues=1001 > 1000).
              It simultaneously reveals the defect: dues=1 should also block.
    """
    s = student(outstanding_dues=1001)
    result = registration_decision(s, course())
    assert result == "DUES_BLOCK"


# ---------------------------------------------------------------------------
# WB-14 — STRUCTURAL: cover Line 59 / Branch 58→59 (GAP-2)
# ---------------------------------------------------------------------------

def test_wb14_waitlisted_branch_line59():
    """
    Target  : Condition G1 (course.enrolled > course.capacity) → True, at
              line 58 specifically (after line 48 guard has already passed).
    Path    : Basis Path 9 — the only path reaching line 59.
    Covers  : Line 59 'return "WAITLISTED"'; Branch 58→59.
    Gap     : Line 59 is unreachable with static Course objects because line 48
              traps enrolled>capacity before line 58.  A DynamicEnrollmentCourse
              returns a valid enrolled value on the first read (line 48 guard)
              and an enrolled>capacity value on the second read (line 58 check).
    Mechanism:
              - 1st read of .enrolled (line 48): returns 5  → 0<=5<=10 → valid
              - 2nd read of .enrolled (line 58): returns 11 → 11>10 → WAITLISTED
    """
    dynamic = _DynamicEnrollmentCourse(
        first_enrolled=5,
        second_enrolled=11,
        code="C1",
        credit_hours=3,
        capacity=10,
        prerequisites=set(),
        waitlist=[],
    )
    s = student(completed_courses=set())
    result = registration_decision(s, dynamic)
    assert result == "WAITLISTED"


# ---------------------------------------------------------------------------
# WB-15 — STRUCTURAL: cover Line 71 / Branch 70→71 (GAP-3, True side)
# ---------------------------------------------------------------------------

def test_wb15_register_course_waitlist_appends_new_student():
    """
    Target  : Branch line 70 → True (decision=="WAITLISTED" and student NOT
              already in waitlist) → executes line 71 waitlist.append().
    Covers  : Line 71 'course.waitlist.append(student.student_id)';
              Branch 70→71.
    Gap     : register_course's WAITLISTED branch was unreachable before WB-14
              was introduced.  WB-15 drives register_course() so the append
              line itself is covered.
    """
    dynamic = _DynamicEnrollmentCourse(
        first_enrolled=5,
        second_enrolled=11,
        code="C1",
        credit_hours=3,
        capacity=10,
        prerequisites=set(),
        waitlist=[],
    )
    s = student(completed_courses=set())
    result = register_course(s, dynamic)
    assert result == "WAITLISTED"
    assert "W001" in dynamic.waitlist


# ---------------------------------------------------------------------------
# WB-16 — STRUCTURAL: Branch 70→72 — student already on waitlist (False side)
# ---------------------------------------------------------------------------

def test_wb16_register_course_no_duplicate_on_waitlist():
    """
    Target  : Branch line 70 → False path (student.student_id IS already in
              course.waitlist) → skips line 71, falls through to 'return decision'.
    Covers  : Branch 70→72 (the False branch of the compound condition at line 70).
    Note    : Exercises the idempotency guard: re-registering a waitlisted student
              must not add a duplicate entry.
    """
    dynamic = _DynamicEnrollmentCourse(
        first_enrolled=5,
        second_enrolled=11,
        code="C1",
        credit_hours=3,
        capacity=10,
        prerequisites=set(),
        waitlist=["W001"],          # student already listed
    )
    s = student(completed_courses=set())
    result = register_course(s, dynamic)
    assert result == "WAITLISTED"
    assert dynamic.waitlist.count("W001") == 1   # no duplicate


# ---------------------------------------------------------------------------
# WB-17 / WB-18 — MC/DC pair for prerequisites_satisfied (Condition P)
# ---------------------------------------------------------------------------

def test_wb17_mcdc_prereqs_empty_required_always_true():
    """
    Target  : MC/DC — Condition P ('not required' is True) independent effect.
    Pair    : WB-17 (P=True) vs WB-18 (P=False, Q=False).
    Covers  : prerequisites_satisfied line 39→40 (True branch).
    When P=True the function short-circuits to return True without evaluating Q.
    """
    assert prerequisites_satisfied(set(), set()) is True   # P=T


def test_wb18_mcdc_prereqs_nonempty_required_not_met():
    """
    Target  : MC/DC — Condition P=False, Condition Q=False independent effect.
    Pair    : WB-17 (P=True) vs WB-18 (P=False, Q=False) demonstrates P's effect.
              WB-18 (Q=False) vs WB-19 (Q=True) demonstrates Q's effect.
    Covers  : prerequisites_satisfied line 39→41 (False branch of 'if not required').
    """
    assert prerequisites_satisfied(set(), {"P1"}) is False  # P=F, Q=F


def test_wb19_mcdc_prereqs_nonempty_required_fully_met():
    """
    Target  : MC/DC — Condition Q=True independent effect.
    Pair    : WB-18 (P=F, Q=F, outcome=False) vs WB-19 (P=F, Q=T, outcome=True).
    Covers  : prerequisites_satisfied line 41 — True return from intersection.
    """
    assert prerequisites_satisfied({"P1"}, {"P1"}) is True  # P=F, Q=T


# ---------------------------------------------------------------------------
# WB-20 — Validation order: dues checked before capacity (FR-15 ordering)
# ---------------------------------------------------------------------------

def test_wb20_dues_validation_precedes_capacity_check():
    """
    Target  : Branch priority — negative dues must raise BEFORE capacity guard.
    Covers  : Line 46→47 (raises ValueError("Invalid dues")) with simultaneously
              invalid capacity; confirms no ValueError("Invalid capacity...") raised.
    Path    : Basis Path 1 — entered and exited at node 2→3.
    """
    with pytest.raises(ValueError, match="Invalid dues"):
        registration_decision(
            student(outstanding_dues=-1),
            course(capacity=0, enrolled=0),
        )
