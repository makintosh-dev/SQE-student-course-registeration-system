"""
Black-box test suite for the Student Course Registration System.

Test design methodology:
  - A1: Equivalence Class Partitioning (ECP-01 … ECP-12)
  - A2: Boundary Value Analysis     (BVA-01 … BVA-13)
  - A3: Decision Table Tests        (DT-01  … DT-11)
  - A4: State-change / integration  (ST-01  … ST-10)

All expected results are derived from REQUIREMENTS.md, not from source code.
"""

import pytest
from registration import (
    Student,
    Course,
    check_credit_limit,
    prerequisites_satisfied,
    registration_decision,
    register_course,
    withdraw_course,
)

# ---------------------------------------------------------------------------
# Helper factories (defaults always produce a fully eligible scenario).
# ---------------------------------------------------------------------------

def make_student(**kwargs):
    """Return a Student that is eligible by default; override via kwargs."""
    defaults = dict(
        student_id="S001",
        completed_courses={"CS101", "MATH101"},
        current_credits=12,
        outstanding_dues=0,
        registered_courses=set(),
    )
    defaults.update(kwargs)
    return Student(**defaults)


def make_course(**kwargs):
    """Return a Course with one open seat by default; override via kwargs."""
    defaults = dict(
        code="CS201",
        credit_hours=3,
        capacity=30,
        enrolled=10,
        prerequisites={"CS101", "MATH101"},
        waitlist=[],
    )
    defaults.update(kwargs)
    return Course(**defaults)


# ===========================================================================
# A1 — Equivalence Class Partitioning (ECP-01 … ECP-12)
# ===========================================================================

# ---------------------------------------------------------------------------
# ECP-01..04  credit_hours valid / invalid equivalence classes
# FR-02: current_credits valid=[0..18], invalid=<0 or >18
#         new_credits     valid=[1..4],  invalid=<1 or >4
# ---------------------------------------------------------------------------

class TestECP_CreditHoursClasses:

    # ECP-01: valid current_credits [0..18] AND valid course credits [1..4]
    # Representative: current=10, new=3  → True (10+3=13 ≤ 18)
    def test_ecp01_valid_current_and_new_credits(self):
        """ECP-01: Both inputs in valid ranges → returns bool (no exception)."""
        result = check_credit_limit(10, 3)
        assert isinstance(result, bool)

    # ECP-02: invalid current_credits below range → ValueError
    def test_ecp02_current_credits_below_zero(self):
        """ECP-02: current_credits = -1 (below 0) → ValueError 'Invalid current credits'."""
        with pytest.raises(ValueError, match="Invalid current credits"):
            check_credit_limit(-1, 3)

    # ECP-03: invalid current_credits above range → ValueError
    def test_ecp03_current_credits_above_max(self):
        """ECP-03: current_credits = 19 (above 18) → ValueError 'Invalid current credits'."""
        with pytest.raises(ValueError, match="Invalid current credits"):
            check_credit_limit(19, 3)

    # ECP-04: invalid new course credits below range → ValueError
    def test_ecp04_course_credits_below_one(self):
        """ECP-04: new_credits = 0 (below 1) → ValueError 'Invalid course credits'."""
        with pytest.raises(ValueError, match="Invalid course credits"):
            check_credit_limit(10, 0)

    # ECP-05: invalid new course credits above range → ValueError
    def test_ecp05_course_credits_above_four(self):
        """ECP-05: new_credits = 5 (above 4) → ValueError 'Invalid course credits'."""
        with pytest.raises(ValueError, match="Invalid course credits"):
            check_credit_limit(10, 5)


# ---------------------------------------------------------------------------
# ECP-06..08  outstanding_dues equivalence classes  (FR-04)
# ---------------------------------------------------------------------------

class TestECP_DuesClasses:

    # ECP-06: dues = 0 (zero — no block)
    def test_ecp06_dues_zero_no_block(self):
        """ECP-06: dues=0 → registration proceeds past dues check."""
        result = registration_decision(make_student(outstanding_dues=0), make_course())
        assert result == "REGISTERED"

    # ECP-07: dues > 0 (positive — blocked)
    def test_ecp07_dues_positive_block(self):
        """ECP-07: dues=500 (positive) → DUES_BLOCK per FR-04."""
        result = registration_decision(make_student(outstanding_dues=500), make_course())
        assert result == "DUES_BLOCK"

    # ECP-08: dues < 0 (invalid — ValueError)
    def test_ecp08_dues_negative_raises(self):
        """ECP-08: dues=-1 (negative) → ValueError 'Invalid dues' per FR-15."""
        with pytest.raises(ValueError, match="Invalid dues"):
            registration_decision(make_student(outstanding_dues=-1), make_course())


# ---------------------------------------------------------------------------
# ECP-09..10  prerequisites equivalence classes  (FR-03, FR-06)
# ---------------------------------------------------------------------------

class TestECP_PrerequisitesClasses:

    # ECP-09: no prerequisites required → always satisfied
    def test_ecp09_no_prerequisites_always_pass(self):
        """ECP-09: required=∅ → prerequisites_satisfied returns True."""
        assert prerequisites_satisfied(set(), set()) is True

    # ECP-10: all required prerequisites completed → satisfied
    def test_ecp10_all_prerequisites_completed(self):
        """ECP-10: completed ⊇ required → True."""
        assert prerequisites_satisfied({"CS101", "MATH101"}, {"CS101", "MATH101"}) is True

    # ECP-11: some (but not all) prerequisites missing → not satisfied
    def test_ecp11_some_prerequisites_missing(self):
        """ECP-11: completed={CS101}, required={CS101,MATH101} → False (FR-03: every course needed)."""
        assert prerequisites_satisfied({"CS101"}, {"CS101", "MATH101"}) is False

    # ECP-12: completed set is empty, prerequisites required → not satisfied
    def test_ecp12_no_courses_completed_prerequisites_required(self):
        """ECP-12: completed=∅, required={CS101} → False."""
        assert prerequisites_satisfied(set(), {"CS101"}) is False


# ===========================================================================
# A2 — Boundary Value Analysis (BVA-01 … BVA-13)
# ===========================================================================

# ---------------------------------------------------------------------------
# BVA-01..06  current_credits boundaries for check_credit_limit  (FR-01, FR-02)
# ---------------------------------------------------------------------------

class TestBVA_CurrentCreditBoundaries:

    # BVA-01: current_credits = 0 (minimum valid)
    def test_bva01_current_credits_zero_min(self):
        """BVA-01: current=0, new=1 → 0+1=1 ≤ 18 → True."""
        assert check_credit_limit(0, 1) is True

    # BVA-02: current_credits = 18 (maximum valid)
    def test_bva02_current_credits_18_max(self):
        """BVA-02: current=18, new=1 → 18+1=19 > 18 → False."""
        assert check_credit_limit(18, 1) is False

    # BVA-03: current_credits = -1 (just outside lower bound → error)
    def test_bva03_current_credits_minus_one_invalid(self):
        """BVA-03: current=-1 → ValueError 'Invalid current credits'."""
        with pytest.raises(ValueError, match="Invalid current credits"):
            check_credit_limit(-1, 1)

    # BVA-04: current_credits = 19 (just outside upper bound → error)
    def test_bva04_current_credits_19_invalid(self):
        """BVA-04: current=19 → ValueError 'Invalid current credits'."""
        with pytest.raises(ValueError, match="Invalid current credits"):
            check_credit_limit(19, 1)


# ---------------------------------------------------------------------------
# BVA-05..07  course credit_hours boundaries  (FR-01, FR-02)
# ---------------------------------------------------------------------------

class TestBVA_CourseCreditsHoursBoundaries:

    # BVA-05: new_credits = 1 (minimum valid)
    def test_bva05_new_credits_one_min(self):
        """BVA-05: current=10, new=1 → 10+1=11 ≤ 18 → True."""
        assert check_credit_limit(10, 1) is True

    # BVA-06: new_credits = 4 (maximum valid)
    def test_bva06_new_credits_four_max(self):
        """BVA-06: current=10, new=4 → 10+4=14 ≤ 18 → True."""
        assert check_credit_limit(10, 4) is True

    # BVA-07: new_credits = 0 (just outside lower bound → error)
    def test_bva07_new_credits_zero_invalid(self):
        """BVA-07: new=0 → ValueError 'Invalid course credits'."""
        with pytest.raises(ValueError, match="Invalid course credits"):
            check_credit_limit(10, 0)

    # BVA-08: new_credits = 5 (just outside upper bound → error)
    def test_bva08_new_credits_five_invalid(self):
        """BVA-08: new=5 → ValueError 'Invalid course credits'."""
        with pytest.raises(ValueError, match="Invalid course credits"):
            check_credit_limit(10, 5)


# ---------------------------------------------------------------------------
# BVA-09..10  combined 18-credit limit boundary  (FR-01)
# ---------------------------------------------------------------------------

class TestBVA_CombinedCreditLimit:

    # BVA-09: exactly 18 combined → allowed (FR-01 says ≤ 18 is allowed)
    def test_bva09_combined_exactly_18_allowed(self):
        """BVA-09: current=15, new=3 → 15+3=18 exactly → True (FR-01: ≤18 allowed)."""
        assert check_credit_limit(15, 3) is True

    # BVA-10: combined = 19 → rejected
    def test_bva10_combined_19_rejected(self):
        """BVA-10: current=16, new=3 → 16+3=19 > 18 → False."""
        assert check_credit_limit(16, 3) is False

    # BVA-11: combined = 17 (one below limit) → allowed
    def test_bva11_combined_17_allowed(self):
        """BVA-11: current=14, new=3 → 14+3=17 ≤ 18 → True."""
        assert check_credit_limit(14, 3) is True


# ---------------------------------------------------------------------------
# BVA-12..13  seat availability boundaries  (FR-08)
# ---------------------------------------------------------------------------

class TestBVA_SeatAvailability:

    # BVA-12: enrolled = capacity (full) → WAITLISTED
    def test_bva12_enrolled_equals_capacity_waitlisted(self):
        """BVA-12: enrolled=30, capacity=30 → WAITLISTED per FR-08."""
        s = make_student()
        c = make_course(enrolled=30, capacity=30)
        assert registration_decision(s, c) == "WAITLISTED"

    # BVA-13: enrolled = capacity - 1 (one seat left) → REGISTERED
    def test_bva13_one_seat_remaining_registered(self):
        """BVA-13: enrolled=29, capacity=30 → REGISTERED per FR-08."""
        s = make_student()
        c = make_course(enrolled=29, capacity=30)
        assert registration_decision(s, c) == "REGISTERED"


# ---------------------------------------------------------------------------
# BVA extra: dues boundary at 0 and 1  (FR-04)
# ---------------------------------------------------------------------------

class TestBVA_DuesBoundary:

    def test_bva_dues_zero_not_blocked(self):
        """dues=0 → not blocked (FR-04: >0 blocks)."""
        assert registration_decision(make_student(outstanding_dues=0), make_course()) == "REGISTERED"

    def test_bva_dues_one_blocked(self):
        """dues=1 → DUES_BLOCK (FR-04: any positive amount blocks)."""
        assert registration_decision(make_student(outstanding_dues=1), make_course()) == "DUES_BLOCK"


# ===========================================================================
# A3 — Decision Table Tests (DT-01 … DT-11)
#
# Conditions (checked in priority order per FR-09):
#   C1: outstanding_dues > 0
#   C2: course already in registered_courses
#   C3: prerequisites NOT satisfied
#   C4: current + course credits > 18
#   C5: enrolled == capacity  (full)
#
# Outcomes: DUES_BLOCK | ALREADY_REGISTERED | PREREQUISITES_MISSING |
#           CREDIT_LIMIT | WAITLISTED | REGISTERED
# ===========================================================================

class TestDecisionTable:

    # DT-01: All conditions false → REGISTERED
    def test_dt01_all_conditions_false_registered(self):
        """DT-01: No dues, not duplicate, prereqs met, credits ok, seat free → REGISTERED."""
        s = make_student(outstanding_dues=0, current_credits=12)
        c = make_course(enrolled=10, capacity=30)
        assert registration_decision(s, c) == "REGISTERED"

    # DT-02: C1=T (dues) → DUES_BLOCK regardless of everything else
    def test_dt02_dues_blocks_all(self):
        """DT-02: dues>0, duplicate, no prereqs, over credit, full → DUES_BLOCK (priority 1)."""
        s = make_student(
            outstanding_dues=1,
            registered_courses={"CS201"},
            completed_courses=set(),
            current_credits=18,
        )
        c = make_course(enrolled=30, capacity=30)
        assert registration_decision(s, c) == "DUES_BLOCK"

    # DT-03: C1=F, C2=T → ALREADY_REGISTERED (priority 2 beats prereqs/credits/seats)
    def test_dt03_duplicate_registration(self):
        """DT-03: No dues, already registered → ALREADY_REGISTERED."""
        s = make_student(outstanding_dues=0, registered_courses={"CS201"})
        c = make_course()
        assert registration_decision(s, c) == "ALREADY_REGISTERED"

    # DT-04: C1=F, C2=F, C3=T → PREREQUISITES_MISSING
    def test_dt04_prerequisites_missing(self):
        """DT-04: No dues, not duplicate, prereqs missing → PREREQUISITES_MISSING."""
        s = make_student(completed_courses=set())
        c = make_course()
        assert registration_decision(s, c) == "PREREQUISITES_MISSING"

    # DT-05: C1=F, C2=F, C3=F, C4=T → CREDIT_LIMIT
    def test_dt05_credit_limit_exceeded(self):
        """DT-05: prereqs ok, credits would exceed 18 → CREDIT_LIMIT."""
        s = make_student(current_credits=16)   # 16+3=19 > 18
        c = make_course(credit_hours=3)
        assert registration_decision(s, c) == "CREDIT_LIMIT"

    # DT-06: C1=F, C2=F, C3=F, C4=F, C5=T → WAITLISTED
    def test_dt06_course_full_waitlisted(self):
        """DT-06: All ok except course full → WAITLISTED."""
        s = make_student(current_credits=12)
        c = make_course(enrolled=30, capacity=30)
        assert registration_decision(s, c) == "WAITLISTED"

    # DT-07: C1=F, C2=T, C3=T → ALREADY_REGISTERED wins over PREREQUISITES_MISSING
    def test_dt07_priority_duplicate_before_prerequisites(self):
        """DT-07: Duplicate AND missing prereqs → ALREADY_REGISTERED (priority 2 > 3)."""
        s = make_student(registered_courses={"CS201"}, completed_courses=set())
        c = make_course()
        assert registration_decision(s, c) == "ALREADY_REGISTERED"

    # DT-08: C1=F, C3=T, C4=T → PREREQUISITES_MISSING wins over CREDIT_LIMIT
    def test_dt08_priority_prerequisites_before_credit_limit(self):
        """DT-08: Missing prereqs AND over credit → PREREQUISITES_MISSING (priority 3 > 4)."""
        s = make_student(completed_courses={"CS101"}, current_credits=18)
        # only CS101 done, requires CS101+MATH101 → prereqs not met
        c = make_course()  # requires {"CS101", "MATH101"}
        assert registration_decision(s, c) == "PREREQUISITES_MISSING"

    # DT-09: C1=F, C4=T, C5=T → CREDIT_LIMIT wins over WAITLISTED
    def test_dt09_priority_credit_limit_before_waitlist(self):
        """DT-09: Over credit AND course full → CREDIT_LIMIT (priority 4 > 5)."""
        s = make_student(current_credits=16)   # 16+3=19 > 18
        c = make_course(enrolled=30, capacity=30)
        assert registration_decision(s, c) == "CREDIT_LIMIT"

    # DT-10: C1=T, C4=T — dues supersedes credit_limit
    def test_dt10_dues_supersedes_credit_limit(self):
        """DT-10: Dues AND over credit → DUES_BLOCK (priority 1 > 4)."""
        s = make_student(outstanding_dues=1, current_credits=18)
        c = make_course()
        assert registration_decision(s, c) == "DUES_BLOCK"

    # DT-11: C1=T, C5=T — dues supersedes waitlist
    def test_dt11_dues_supersedes_waitlist(self):
        """DT-11: Dues AND course full → DUES_BLOCK (priority 1 > 5)."""
        s = make_student(outstanding_dues=100)
        c = make_course(enrolled=30, capacity=30)
        assert registration_decision(s, c) == "DUES_BLOCK"


# ===========================================================================
# A4 — State-change / integration tests (ST-01 … ST-10)
# ===========================================================================

class TestStateChanges:

    # ST-01: Successful registration updates all three state variables  (FR-11)
    def test_st01_successful_registration_updates_state(self):
        """ST-01: REGISTERED → course added, credits increased, enrollment incremented."""
        s = make_student(current_credits=12)
        c = make_course(enrolled=10, credit_hours=3)
        result = register_course(s, c)
        assert result == "REGISTERED"
        assert "CS201" in s.registered_courses, "Course code must be added to registered_courses"
        assert s.current_credits == 15, "Credits must increase by course credit_hours (3)"
        assert c.enrolled == 11, "Course enrollment must increment by 1"

    # ST-02: REGISTERED does not add student to waitlist  (FR-11)
    def test_st02_successful_registration_no_waitlist_entry(self):
        """ST-02: Successful registration must not append to waitlist."""
        s = make_student()
        c = make_course(enrolled=10)
        register_course(s, c)
        assert s.student_id not in c.waitlist

    # ST-03: WAITLISTED appends student ID once (FR-12)
    def test_st03_waitlist_appends_student_once(self):
        """ST-03: Calling register_course twice when full adds the ID exactly once."""
        s = make_student()
        c = make_course(enrolled=30, capacity=30)
        r1 = register_course(s, c)
        r2 = register_course(s, c)
        assert r1 == "WAITLISTED"
        assert r2 == "WAITLISTED"
        assert c.waitlist.count(s.student_id) == 1, "Student ID must appear in waitlist exactly once"

    # ST-04: WAITLISTED does not change credits or registered_courses or enrollment (FR-12)
    def test_st04_waitlist_no_credits_or_enrollment_change(self):
        """ST-04: WAITLISTED → credits, registered_courses, enrolled must be unchanged."""
        s = make_student(current_credits=12)
        c = make_course(enrolled=30, capacity=30)
        credits_before = s.current_credits
        registered_before = set(s.registered_courses)
        enrolled_before = c.enrolled
        register_course(s, c)
        assert s.current_credits == credits_before
        assert s.registered_courses == registered_before
        assert c.enrolled == enrolled_before

    # ST-05: DUES_BLOCK leaves state unchanged (FR-10, FR-12 by analogy)
    def test_st05_dues_block_no_state_change(self):
        """ST-05: DUES_BLOCK must not alter student or course state."""
        s = make_student(outstanding_dues=500)
        c = make_course(enrolled=10)
        credits_before = s.current_credits
        registered_before = set(s.registered_courses)
        enrolled_before = c.enrolled
        waitlist_before = list(c.waitlist)
        result = register_course(s, c)
        assert result == "DUES_BLOCK"
        assert s.current_credits == credits_before
        assert s.registered_courses == registered_before
        assert c.enrolled == enrolled_before
        assert c.waitlist == waitlist_before

    # ST-06: ALREADY_REGISTERED leaves state unchanged (FR-10)
    def test_st06_already_registered_no_state_change(self):
        """ST-06: ALREADY_REGISTERED must not alter any state."""
        s = make_student(registered_courses={"CS201"}, current_credits=12)
        c = make_course(enrolled=10)
        credits_before = s.current_credits
        registered_before = set(s.registered_courses)
        enrolled_before = c.enrolled
        result = register_course(s, c)
        assert result == "ALREADY_REGISTERED"
        assert s.current_credits == credits_before
        assert s.registered_courses == registered_before
        assert c.enrolled == enrolled_before

    # ST-07: PREREQUISITES_MISSING leaves state unchanged (FR-10)
    def test_st07_prerequisites_missing_no_state_change(self):
        """ST-07: PREREQUISITES_MISSING must not alter any state."""
        s = make_student(completed_courses=set())
        c = make_course(enrolled=10)
        credits_before = s.current_credits
        registered_before = set(s.registered_courses)
        enrolled_before = c.enrolled
        result = register_course(s, c)
        assert result == "PREREQUISITES_MISSING"
        assert s.current_credits == credits_before
        assert s.registered_courses == registered_before
        assert c.enrolled == enrolled_before

    # ST-08: CREDIT_LIMIT leaves state unchanged (FR-10)
    def test_st08_credit_limit_no_state_change(self):
        """ST-08: CREDIT_LIMIT must not alter any state."""
        s = make_student(current_credits=16)   # 16+3=19 > 18
        c = make_course(enrolled=10)
        credits_before = s.current_credits
        registered_before = set(s.registered_courses)
        enrolled_before = c.enrolled
        result = register_course(s, c)
        assert result == "CREDIT_LIMIT"
        assert s.current_credits == credits_before
        assert s.registered_courses == registered_before
        assert c.enrolled == enrolled_before

    # ST-09: Successful withdrawal updates all state  (FR-13)
    def test_st09_withdrawal_updates_state(self):
        """ST-09: withdraw_course returns True, removes course, reduces credits, decrements enrollment."""
        s = make_student(registered_courses={"CS201"}, current_credits=15)
        c = make_course(enrolled=11, credit_hours=3)
        result = withdraw_course(s, c)
        assert result is True
        assert "CS201" not in s.registered_courses, "Course must be removed from registered_courses"
        assert s.current_credits == 12, "Credits must decrease by course credit_hours (3)"
        assert c.enrolled == 10, "Course enrollment must decrement by 1 (FR-13)"

    # ST-10: Withdrawing unregistered course returns False and leaves state unchanged (FR-14)
    def test_st10_withdrawal_not_registered_no_change(self):
        """ST-10: withdraw_course on unregistered course returns False and alters nothing."""
        s = make_student()   # registered_courses=set() → CS201 not registered
        c = make_course(enrolled=10)
        credits_before = s.current_credits
        registered_before = set(s.registered_courses)
        enrolled_before = c.enrolled
        result = withdraw_course(s, c)
        assert result is False
        assert s.current_credits == credits_before
        assert s.registered_courses == registered_before
        assert c.enrolled == enrolled_before


# ===========================================================================
# A4 — Validation / error-handling (prerequisite to above)
# ===========================================================================

class TestInputValidation:

    def test_negative_dues_raises_before_capacity(self):
        """FR-15: dues validated first; negative dues raises even if capacity is also invalid."""
        with pytest.raises(ValueError, match="Invalid dues"):
            registration_decision(
                make_student(outstanding_dues=-1),
                make_course(capacity=0),
            )

    @pytest.mark.parametrize("capacity,enrolled", [
        (0, 0),   # capacity < 1
        (3, -1),  # enrolled < 0
        (3, 4),   # enrolled > capacity
    ])
    def test_invalid_capacity_or_enrollment_raises(self, capacity, enrolled):
        """FR-15: capacity < 1 or enrolled ∉ [0, capacity] → ValueError."""
        with pytest.raises(ValueError, match="Invalid capacity or enrollment"):
            registration_decision(make_student(), make_course(capacity=capacity, enrolled=enrolled))

    def test_error_check_order_current_before_new_credits(self):
        """FR-02: current_credits validated before new_credits when both invalid."""
        with pytest.raises(ValueError, match="Invalid current credits"):
            check_credit_limit(-1, 0)   # both invalid; current checked first
